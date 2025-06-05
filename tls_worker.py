import socket
from gunicorn.workers.sync import SyncWorker

class TLSDroppingWorker(SyncWorker):
    """Gunicorn worker that ignores TLS handshake attempts on plain HTTP ports."""

    def handle(self, listener, client, addr):
        try:
            client.settimeout(0.5)
            peek = client.recv(3, socket.MSG_PEEK)
            client.settimeout(None)
            if peek and len(peek) >= 3 and peek.startswith(b"\x16\x03"):
                self.log.debug("Ignored TLS handshake attempt")
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                client.close()
                return
        except socket.timeout:
            client.settimeout(None)
        except Exception as exc:
            client.settimeout(None)
            if "\x16\x03" in repr(exc):
                self.log.debug("Ignored TLS handshake attempt during peek: %s", exc)
                try:
                    client.close()
                except Exception:
                    pass
                return
        super().handle(listener, client, addr)

