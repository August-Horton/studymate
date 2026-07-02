const { app, BrowserWindow, ipcMain, session } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const os = require('os')
const http = require('http')

let mainWindow
let backendProcess
let healthCheckInterval
const BACKEND_PORT = 8000
const BACKEND_HOST = 'localhost'
const HEALTH_CHECK_INTERVAL = 5000
const MAX_RESTART_ATTEMPTS = 3
let restartAttempts = 0

function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(`http://${BACKEND_HOST}:${BACKEND_PORT}/api/test-connection`, (res) => {
      if (res.statusCode === 200) {
        resolve({ healthy: true })
      } else {
        resolve({ healthy: false, error: `Status code: ${res.statusCode}` })
      }
    })
    
    req.on('error', (err) => {
      resolve({ healthy: false, error: err.message })
    })
    
    req.setTimeout(3000, () => {
      req.destroy()
      resolve({ healthy: false, error: 'Timeout' })
    })
  })
}

async function monitorBackend() {
  if (!backendProcess || backendProcess.killed) {
    console.log('Backend process not running, attempting to start...')
    startBackend()
    return
  }

  const health = await checkBackendHealth()
  
  if (health.healthy) {
    if (restartAttempts > 0) {
      console.log('Backend recovered, reset restart attempts')
      restartAttempts = 0
    }
    
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend-status', { status: 'healthy' })
    }
  } else {
    console.log(`Backend unhealthy: ${health.error}`)
    
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend-status', { status: 'unhealthy', error: health.error })
    }
    
    if (restartAttempts < MAX_RESTART_ATTEMPTS) {
      console.log(`Attempting to restart backend (attempt ${restartAttempts + 1}/${MAX_RESTART_ATTEMPTS})...`)
      restartAttempts++
      
      stopBackend()
      await new Promise(resolve => setTimeout(resolve, 1000))
      startBackend()
    } else {
      console.log('Max restart attempts reached, manual intervention required')
      
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend-status', { 
          status: 'failed', 
          error: '后端多次重启失败，请手动重启应用' 
        })
      }
    }
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  })

  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
    if (details.url.startsWith('file://') && details.url.includes('/api/')) {
      const apiPath = details.url.replace(/^file:\/\/[^/]+\/api\//, 'http://localhost:8000/api/')
      callback({ redirectURL: apiPath })
    } else {
      callback({ cancel: false })
    }
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
  }

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`Failed to load: ${errorDescription} (${errorCode})`)
  })

  mainWindow.webContents.on('crashed', () => {
    console.error('Renderer process crashed')
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function startBackend() {
  let backendPath
  let exePath

  if (process.env.NODE_ENV === 'development') {
    backendPath = path.join(__dirname, '../backend')
    backendProcess = spawn('python', ['main.py'], {
      cwd: backendPath,
      shell: true
    })
  } else {
    backendPath = path.join(process.resourcesPath, 'backend')
    exePath = process.platform === 'win32'
      ? path.join(backendPath, 'main.exe')
      : path.join(backendPath, 'main')
    
    console.log(`Backend path: ${backendPath}`)
    console.log(`Exe path: ${exePath}`)
    console.log(`Resources path: ${process.resourcesPath}`)
    
    const fs = require('fs')
    if (fs.existsSync(exePath)) {
      console.log('Backend executable exists')
    } else {
      console.log('Backend executable NOT found:', exePath)
    }
    
    backendProcess = spawn(exePath, [], {
      cwd: backendPath,
      shell: true
    })
  }

  backendProcess.stdout.on('data', (data) => {
    console.log(`后端输出: ${data}`)
  })

  backendProcess.stderr.on('data', (data) => {
    console.error(`后端错误: ${data}`)
  })

  backendProcess.on('close', (code) => {
    console.log(`后端进程退出，代码: ${code}`)
    if (code !== 0 && code !== null) {
      console.log('Backend exited with non-zero code, may need restart')
    }
  })
  
  backendProcess.on('error', (err) => {
    console.error('启动后端失败:', err)
  })
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

function startHealthCheck() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval)
  }
  
  healthCheckInterval = setInterval(monitorBackend, HEALTH_CHECK_INTERVAL)
  console.log(`Started backend health check every ${HEALTH_CHECK_INTERVAL}ms`)
}

function stopHealthCheck() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval)
    healthCheckInterval = null
  }
}

app.whenReady().then(() => {
  startBackend()
  startHealthCheck()
  
  setTimeout(createWindow, 8000)

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  stopHealthCheck()
  stopBackend()
})

app.on('will-quit', () => {
  stopHealthCheck()
  stopBackend()
})

ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

ipcMain.handle('get-backend-status', async () => {
  return await checkBackendHealth()
})

ipcMain.handle('restart-backend', async () => {
  console.log('Manual backend restart requested')
  restartAttempts = 0
  stopBackend()
  await new Promise(resolve => setTimeout(resolve, 1000))
  startBackend()
  return { success: true, message: 'Backend restart initiated' }
})
