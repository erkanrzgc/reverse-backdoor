"""TUI for reverse-backdoor C2 framework using Textual."""


class TuiApp:
    """Terminal UI for managing reverse-backdoor agents.

    Requires: pip install textual

    Usage:
        python -m server.tui
    """

    def run(self):
        try:
            from textual.app import App
        except ImportError:
            print("Textual not installed. Install with: pip install textual")
            return

        from textual.app import App, ComposeResult
        from textual.containers import Container, Horizontal
        from textual.widgets import Header, Footer, Static, Input, ListView, ListItem
        from textual.screen import Screen
        from textual.binding import Binding

        from server.core.agent_registry import AgentRegistry
        from server.core.protocol import Protocol
        from server.commands import build_server_router
        from server.commands.base import ServerSessionContext

        import threading
        import time

        registry = AgentRegistry()

        class AgentList(Static):
            def on_mount(self):
                self.update_display()
                self.set_interval(1, self.update_display)

            def update_display(self):
                agents = registry.list_all()
                if not agents:
                    self.update("[dim]No agents connected[/dim]")
                    return
                lines = []
                for aid, info in agents.items():
                    lines.append(f"[cyan]{info.agent_id}[/cyan]  {info.ip}")
                self.update("\n".join(lines))

        class OutputPanel(Static):
            pass

        class CommandInput(Input):
            pass

        class MainScreen(Screen):
            BINDINGS = [
                Binding("q", "quit", "Quit"),
                Binding("r", "refresh", "Refresh"),
            ]

            def compose(self) -> ComposeResult:
                yield Header()
                yield Container(
                    Horizontal(
                        Container(Static("[bold]Agents[/bold]"), AgentList(id="agent-list"), id="sidebar"),
                        Container(
                            Static("[bold]Output[/bold]", id="output-title"),
                            OutputPanel(id="output"),
                            CommandInput(placeholder="REVERSE_BACKDOOR> ", id="cmd-input"),
                            id="main",
                        ),
                    ),
                )
                yield Footer()

            def action_refresh(self):
                self.query_one("#agent-list", AgentList).update_display()

            def on_input_submitted(self, event):
                cmd_input = event.input
                command = cmd_input.value.strip()
                cmd_input.value = ""
                output = self.query_one("#output", OutputPanel)

                if command == "agents":
                    agents = registry.list_all()
                    if not agents:
                        output.update("[yellow]No agents connected[/yellow]")
                    else:
                        lines = []
                        for aid, info in agents.items():
                            lines.append(f"  {info.agent_id}  {info.ip}")
                        output.update("\n".join(lines))
                elif command == "help":
                    output.update("[cyan]agents | interact <id> | broadcast <cmd> | exit[/cyan]")
                elif command == "exit":
                    self.app.exit()
                elif command.startswith("interact "):
                    target_id = command[9:].strip()
                    info = registry.get(target_id)
                    if info is None:
                        output.update(f"[red]Agent '{target_id}' not found[/red]")
                    else:
                        output.update(f"[green]Interacting with {target_id}[/green]")
                elif command.startswith("broadcast "):
                    cmd = command[10:].strip()
                    registry.broadcast(cmd)
                    output.update(f"[green]Broadcast sent: {cmd}[/green]")
                else:
                    output.update(f"[red]Unknown command: {command}[/red]")

        class ReverseBackdoorApp(App):
            CSS = """
            #sidebar {
                width: 30%;
                border: solid $primary;
                padding: 1;
            }
            #main {
                width: 70%;
                border: solid $primary;
                padding: 1;
            }
            #output {
                height: 80%;
                overflow-y: auto;
            }
            #cmd-input {
                dock: bottom;
            }
            """

            def on_mount(self):
                self.push_screen(MainScreen())

        app = ReverseBackdoorApp()
        app.run()
