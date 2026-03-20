#!/usr/bin/env python3
import asyncio
import os
import sys
import pathlib
import pty
import signal
from aiohttp import web, WSMsgType


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


def main():
    app = web.Application()
    app.add_routes([
        web.get('/', index),
        web.get('/ws', websocket_handler),
    ])
    app.router.add_static('/static/', pathlib.Path(__file__).parent / 'static')
    web.run_app(app, port=8080)


if __name__ == '__main__':
    main()
