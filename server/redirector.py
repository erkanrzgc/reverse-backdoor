import asyncio
import ssl
import logging
from typing import Optional

logger = logging.getLogger("redirector")


class Redirector:
    def __init__(self, listen_host: str, listen_port: int,
                 target_host: str, target_port: int, tls_cert: Optional[str] = None,
                 tls_key: Optional[str] = None):
        self._lhost, self._lport = listen_host, listen_port
        self._thost, self._tport = target_host, target_port
        self._server = None
        self._ssl = None
        if tls_cert and tls_key:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(tls_cert, tls_key)
            self._ssl = ctx

    async def start(self):
        async def handler(r: asyncio.StreamReader, w: asyncio.StreamWriter):
            peer = w.get_extra_info('peername')
            logger.info(f"redirector {self._lhost}:{self._lport} <- {peer}")
            try:
                tr, tw = await asyncio.open_connection(self._thost, self._tport)
                async def pipe(rd, wr):
                    while True:
                        data = await rd.read(65536)
                        if not data:
                            break
                        wr.write(data)
                        await wr.drain()
                    wr.close()
                await asyncio.gather(pipe(r, tw), pipe(tr, w))
            except Exception as e:
                logger.error(f"redirector pipe error: {e}")
            finally:
                try:
                    w.close()
                except Exception:
                    pass

        self._server = await asyncio.start_server(
            handler, self._lhost, self._lport, ssl=self._ssl)
        logger.info(f"redirector {self._lhost}:{self._lport} -> {self._thost}:{self._tport}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()


class RedirectorPool:
    def __init__(self):
        self._redirectors: dict = {}
        self._tasks: dict = {}

    async def add(self, name: str, listen_host: str, listen_port: int,
                  target_host: str, target_port: int, tls_cert: str = None, tls_key: str = None):
        if name in self._redirectors:
            raise ValueError(f"redirector {name} already exists")
        r = Redirector(listen_host, listen_port, target_host, target_port, tls_cert, tls_key)
        self._redirectors[name] = r
        self._tasks[name] = asyncio.create_task(r.start())

    async def remove(self, name: str):
        r = self._redirectors.pop(name, None)
        if r is None:
            return
        task = self._tasks.pop(name, None)
        await r.stop()
        if task:
            task.cancel()

    def status(self) -> dict:
        return {name: {"listen": f"{r._lhost}:{r._lport}",
                       "target": f"{r._thost}:{r._tport}"}
                for name, r in self._redirectors.items()}
