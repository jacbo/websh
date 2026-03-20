# websh:一款web版的shell工具

## 功能简介

1. 在chrome浏览器访问安装websh的Linux服务器，可以通过浏览器访问linux服务器的bash交互功能
2. 多会话支持,页面左侧可以新建多个shell交互会话。右侧显示当前会话的bash主页面。

## 开发及运行环境

1. 该系统运行操作系统为Linux
2. 开发语言主要为python3,并已通过uv init命令创建好目录结构
3. 系统默认端口为8080,访问地址为http://ip:port


### 部署

1. 程序入口文件为main.py
2. 执行uv run main.py 或 激活当前python环境执行python main.py来启动服务。

### 新增功能

1. 前端集成 `xterm.js` 提供真实终端交互体验，支持字符渲染、颜色与光标控制。
2. 多会话支持：左侧可新建多个终端会话，点击切换会话。
3. PTY 后端：使用 WebSocket 将浏览器输入转发到服务器的 PTY（bash），并把输出推回浏览器。
4. 窗口自适应：前端使用 `xterm-addon-fit` 自动调整终端行列数，后端支持 PTY 窗口大小调整。
5. 可拖拽侧栏：左侧栏宽度可以通过鼠标拖动实时调整，调整会触发终端 `fit()`。
6. UI 优化：使用 Font Awesome 图标增强按钮可识别性，默认 `新建` 使用 `fa-plus`，`关闭` 使用 `fa-trash`（删除当前会话）。

运行与测试：

```bash
pip install aiohttp
python main.py
# 浏览器访问 http://localhost:8080
```

注意：该项目依赖 POSIX PTY，推荐部署在 Linux 服务器；在 Windows 上会降级为交互式 Python 子进程，行为不同。
