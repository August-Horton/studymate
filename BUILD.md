# StudyMate 打包指南

本文档介绍如何将 StudyMate 项目打包成可直接分发的桌面应用程序。

## 当前进度

✅ 已完成的工作：
- 创建了 Electron 应用配置
- 成功打包了 Python 后端
- 前端已经构建完成
- 安装了所有必要的依赖

## 前置条件

确保已安装以下工具：
- **Node.js** (v16 或更高版本) - 已安装
- **Python** (v3.8 或更高版本) - 已安装
- **pip** (Python 包管理器) - 已安装

## 已完成步骤

### 1. 安装依赖 ✅
- 根目录 Node.js 依赖已安装
- PyInstaller 已安装

### 2. 打包后端 ✅
Python 后端已成功打包到 `dist/backend/` 目录

### 3. 前端构建 ✅
前端已构建完成，位于 `frontend/dist/` 目录

## 最后一步：打包 Electron 应用

运行以下命令来创建最终的可分发应用：

```bash
npm run electron:build:win
```

这个命令会：
1. 把前端、后端和 Electron 运行时打包在一起
2. 在 `release/` 目录生成两个文件：
   - `StudyMate 智学助手 Setup x.x.x.exe` - Windows 安装程序（推荐）
   - `StudyMate 智学助手 x.x.x.exe` - Windows 便携版（无需安装）

## 开发模式测试（可选）

如果你想在打包前测试应用，可以运行：

```bash
npm run electron:dev
```

这会启动 Electron 开发模式。

## 打包后的使用

用户安装或运行应用后：
1. 应用会自动启动本地服务器
2. 数据库会保存在用户目录下的 `%APPDATA%\StudyMate\`（Windows）
3. 所有功能都可以离线使用（除了需要 API 调用的 AI 功能）

## 注意事项

1. **打包体积**：由于包含了完整的 Python 运行时和所有依赖，应用体积会比较大（几百 MB）
2. **首次启动**：首次启动可能需要几秒钟来启动后端服务
3. **数据保存**：用户数据会保存在系统应用数据目录，卸载应用时不会自动删除

## 故障排除

### 如果打包失败

确保所有文件路径都正确，检查：
- `dist/backend/` 目录存在且包含 `main.exe`
- `frontend/dist/` 目录存在
- `electron/` 目录包含 `main.js` 和 `preload.js`

### 应用启动失败

如果打包后的应用无法启动，请检查：
1. 防火墙是否阻止了本地服务器
2. 端口 8000 是否被占用
3. 查看开发者工具的控制台（按 F12 打开）
