#!/usr/bin/env python3
import asyncio
import os
import sys
import pathlib
import pty
import signal
from aiohttp import web, WSMsgType
import pathlib


async def index(request):
    return web.FileResponse(pathlib.Path(__file__).parent / 'static' / 'index.html')


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    loop = asyncio.get_event_loop()

    if os.name == 'posix':
        pid, master = pty.fork()
        if pid == 0:
            os.execvp('/bin/bash', ['/bin/bash'])

        async def read_pty():
            try:
                while True:
                    data = await loop.run_in_executor(None, os.read, master, 1024)
                    if not data:
                        break
                    text = data.decode('utf-8', errors='replace')
                    await ws.send_str(text)
            except Exception:
                pass

        reader_task = asyncio.create_task(read_pty())

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == '__exit__':
                        break
                    os.write(master, msg.data.encode())
                elif msg.type == WSMsgType.BINARY:
                    os.write(master, msg.data)
                elif msg.type == WSMsgType.CLOSE:
                    break
        finally:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            reader_task.cancel()
            await ws.close()
            await loop.run_in_executor(None, os.close, master)
    else:
        proc = await asyncio.create_subprocess_exec(sys.executable, '-i', stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        #!/usr/bin/env python3
        import asyncio
        import os
        import sys
        import pathlib
        from aiohttp import web, WSMsgType

        INDEX_PATH = pathlib.Path(__file__).parent / 'static' / 'index.html'


        async def index(request):
            return web.FileResponse(INDEX_PATH)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    loop = asyncio.get_event_loop()

    if os.name == 'posix':
        import fcntl
        import termios
        import struct

        master_fd, slave_fd = os.openpty()
        # set non-blocking reads on master
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # spawn bash attached to the slave end
        proc = await asyncio.create_subprocess_exec('/bin/bash', stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)
        os.close(slave_fd)

        async def read_pty():
            try:
                while True:
                    await asyncio.sleep(0)
                    try:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        await ws.send_bytes(data)
                    except BlockingIOError:
                        await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                pass

        reader_task = asyncio.create_task(read_pty())

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    text = msg.data
                    if text.startswith('__resize__:'):
                        # format: __resize__:cols:rows
                        try:
                            _, cols, rows = text.split(':')
                            cols = int(cols)
                            rows = int(rows)
                            winsize = struct.pack('HHHH', rows, cols, 0, 0)
                            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                        except Exception:
                            pass
                    else:
                        try:
                            os.write(master_fd, text.encode())
                        except Exception:
                            pass
                elif msg.type == WSMsgType.BINARY:
                    try:
                        os.write(master_fd, msg.data)
                    except Exception:
                        pass
                elif msg.type == WSMsgType.CLOSE:
                    break
        finally:
            reader_task.cancel()
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                os.close(master_fd)
            except Exception:
                pass
            await ws.close()

    else:
        # fallback for non-posix (simple interactive python)
        proc = await asyncio.create_subprocess_exec(sys.executable, '-i', stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        async def read_proc():
            try:
                while True:
                    data = await proc.stdout.read(1024)
                    if not data:
                        break
                    await ws.send_str(data.decode('utf-8', errors='replace'))
            except asyncio.CancelledError:
                pass

        reader_task = asyncio.create_task(read_proc())

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        proc.stdin.write(msg.data.encode())
                        await proc.stdin.drain()
                    except Exception:
                        pass
                elif msg.type == WSMsgType.CLOSE:
                    break
        finally:
            reader_task.cancel()
            try:
                proc.terminate()
            except Exception:
                pass
            await ws.close()

    return ws


async def upload_handler(request):
    # accept multipart file upload and save to target directory (query param 'dir') or ./uploads
    target_dir_q = request.query.get('dir')
    if target_dir_q:
        target_dir = pathlib.Path(target_dir_q).expanduser()
    else:
        target_dir = pathlib.Path(__file__).parent / 'uploads'
    try:
        target_dir = target_dir.resolve()
    except Exception:
        pass
    target_dir.mkdir(parents=True, exist_ok=True)

    reader = await request.multipart()
    saved = []
    while True:
        field = await reader.next()
        if field is None:
            break
        if field.filename:
            filename = pathlib.Path(field.filename).name
            dest = target_dir / filename
            # write in chunks to file using thread to avoid blocking
            with open(dest, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    await asyncio.to_thread(f.write, chunk)
            saved.append(str(dest))

    return web.json_response({'saved': saved, 'dir': str(target_dir)})


async def list_handler(request):
    dir_q = request.query.get('dir')
    if not dir_q:
        base = pathlib.Path.home()
    else:
        base = pathlib.Path(dir_q).expanduser()
    try:
        base = base.resolve()
    except Exception:
        pass
    items = []
    if base.exists() and base.is_dir():
        try:
            for p in sorted(base.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                st = p.stat()
                items.append({
                    'name': p.name,
                    'path': str(p),
                    'is_dir': p.is_dir(),
                    'size': st.st_size if p.is_file() else 0,
                    'mtime': int(st.st_mtime),
                })
        except PermissionError:
            return web.json_response({'path': str(base), 'items': [], 'error': 'permission denied'}, status=403)
    else:
        return web.json_response({'path': str(base), 'items': [], 'error': 'not a directory'}, status=400)

    return web.json_response({'path': str(base), 'items': items})


async def download_handler(request):
    path_q = request.query.get('path')
    if not path_q:
        return web.Response(status=400, text='missing path')
    p = pathlib.Path(path_q).expanduser()
    try:
        p = p.resolve()
    except Exception:
        pass
    if not p.exists() or not p.is_file():
        return web.Response(status=404, text='not found')
    return web.FileResponse(p)


def main():
    app = web.Application()
    app.add_routes([
        web.get('/', index),
        web.get('/ws', websocket_handler),
        web.post('/upload', upload_handler),
        web.get('/list', list_handler),
        web.get('/download', download_handler),
    ])
    app.router.add_static('/static/', pathlib.Path(__file__).parent / 'static')
    web.run_app(app, port=8080)


if __name__ == '__main__':
    main()
