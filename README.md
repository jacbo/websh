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
# websh — Web Shell（Web 版交互式 Shell）

一个通过浏览器访问服务器 shell 的轻量演示工具，适合作为远程运维或教学演示的原型。

**代码位置**: 项目入口为 `main.py`，前端静态文件在 `static/`。

## 功能概览

- 浏览器内真实终端：使用 `xterm.js` 渲染终端，支持颜色、光标与控制序列。
- 多会话：左侧可新建多个独立的终端会话并切换。
- PTY 后端：服务器端创建 PTY（在 POSIX 环境），通过 WebSocket 与前端交互。
- 可拖拽侧栏：左侧栏宽度可通过鼠标拖动调整，调整时会触发终端自适应。
- 垂直 Tabs：左侧使用竖向 Tab（会话 / 文件上传 / 设置），界面更紧凑。
- 文件管理：在“文件上传”标签下支持上传文件、列出目录、进入子目录和下载文件；列表显示文件大小与修改时间。
- UI 优化：使用 Font Awesome 图标和紧凑按钮风格。

## 开发与运行环境

- 推荐运行环境：Linux（支持 PTY）。
- 语言：Python 3.12+。
- 依赖：`aiohttp`（已在 `pyproject.toml` 中声明）。

### 启动方法

在项目根目录运行：

```bash
pip install aiohttp
python main.py
```

然后在浏览器打开：

		http://localhost:8080

## 前端说明（`static/index.html`）

- 左侧为竖向 Tab：
	- 会话（Sessions）：新建 / 关闭会话、会话列表。
	- 文件上传（Upload）：顶部可输入目标目录（默认为用户主目录），选择文件上传，下方显示该目录文件列表；文件项可下载或进入子目录；列表显示大小与修改时间。
	- 设置（Settings）：占位页面，可扩展。
- 右侧为 `xterm.js` 终端视图，激活会话时自动调用 `fit()`，并将终端大小通过 WebSocket 通知后端 PTY（格式：`__resize__:cols:rows`）。

## 后端 HTTP / WebSocket 接口

- WebSocket 终端： `GET /ws` — 建立 WebSocket，与 PTY 交互（POSIX 环境使用真实 bash PTY；非 POSIX 环境降级为 Python 交互子进程）。
- 文件上传： `POST /upload?dir=<path>` — multipart 上传；若不指定 `dir`，文件将保存到项目 `uploads/` 目录；如果指定 `dir`，会尝试保存到该路径（请注意权限与安全风险）。
- 列表目录： `GET /list?dir=<path>` — 返回目录项（若不指定 `dir` 则列出用户主目录）。
- 下载文件： `GET /download?path=<path>` — 下载指定文件。

接口返回示例（`/list`）：

```json
{ "path": "/home/user", "items": [{"name":"file.txt","path":"/home/user/file.txt","is_dir":false,"size":1234,"mtime":1610000000}, ...] }
```

## 安全与注意事项

- 当前实现为演示/原型，默认允许浏览和上传任意路径（服务器权限允许的情况下）。在生产环境必须严格限制可访问根路径、加入认证与权限校验、并进行输入校验以防目录遍历等风险。
- 建议部署在内网或受控环境，并在前端/后端添加认证（例如基于令牌或 session）。

## 可扩展项（建议）

- 对 `/upload` 添加大小限制、文件类型校验、重名处理。
- 在文件列表中添加搜索与排序功能、文本/图片在线预览。
- 为终端会话添加会话名保存、日志记录与审计功能。

