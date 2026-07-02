const { spawn } = require('child_process');
const path = require('path');

console.log('========================================');
console.log('  StudyMate 智学助手 - 开发模式');
console.log('========================================');
console.log();

let backendProcess;
let frontendProcess;

console.log('正在启动后端...');
backendProcess = spawn('python', ['main.py'], {
  cwd: path.join(__dirname, 'backend'),
  shell: true
});

backendProcess.stdout.on('data', (data) => {
  console.log(`[后端] ${data}`);
});

backendProcess.stderr.on('data', (data) => {
  console.error(`[后端错误] ${data}`);
});

backendProcess.on('close', (code) => {
  console.log(`后端进程退出，代码: ${code}`);
});

console.log('等待 3 秒后启动前端...');
setTimeout(() => {
  console.log('正在启动前端...');
  frontendProcess = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, 'frontend'),
    shell: true
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`[前端] ${data}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`[前端错误] ${data}`);
  });

  frontendProcess.on('close', (code) => {
    console.log(`前端进程退出，代码: ${code}`);
  });
}, 3000);

process.on('SIGINT', () => {
  console.log('\n正在关闭应用...');
  if (backendProcess) backendProcess.kill();
  if (frontendProcess) frontendProcess.kill();
  process.exit();
});
