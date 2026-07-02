const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
}

function startBackend() {
  const backendPath = path.join(__dirname, 'dist/backend');
  const exePath = path.join(backendPath, 'main.exe');
  
  backendProcess = spawn(exePath, [], {
    cwd: backendPath
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`后端: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`后端错误: ${data}`);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

app.whenReady().then(() => {
  startBackend();
  setTimeout(createWindow, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
