from client.core.session_context import SessionContext
from client.commands import build_client_registry
from client.modules.shell import run_command


def handle_session(sock, platform, encryption=False):
    protocol = _build_protocol(sock, encryption)
    ctx = SessionContext(sock=sock, protocol=protocol, platform=platform)
    registry = build_client_registry()

    try:
        while True:
            command = protocol.recv()
            command = command.strip() if isinstance(command, str) else str(command)
            result = registry.dispatch(ctx, command)
            if result is False:
                break
            if result is None:
                run_command(protocol, command, ctx.proc_holder)
    except (ConnectionError, BrokenPipeError, OSError):
        pass
    finally:
        ctx.cleanup()
        try:
            sock.close()
        except Exception:
            pass


def _build_protocol(sock, encryption):
    if encryption:
        from client.core.encrypted_protocol import EncryptedProtocol
        return EncryptedProtocol(sock)
    from client.core.protocol import Protocol
    return Protocol(sock)
