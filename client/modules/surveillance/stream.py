import threading
import time

from .screenshot import screenshot

_state = {'running': False, 'count': 0, 'thread': None, 'lock': threading.Lock()}


def start_stream(protocol, interval_sec=5, count=None):
    with _state['lock']:
        if _state['running']:
            protocol.send('[-] Stream already running')
            return
        _state['running'] = True
        _state['count'] = 0

    def _capture_loop():
        captured = 0
        while _state['running']:
            screenshot(protocol)
            with _state['lock']:
                captured += 1
                _state['count'] = captured
            if count is not None and captured >= count:
                stop_stream()
                break
            time.sleep(interval_sec)

    t = threading.Thread(target=_capture_loop, daemon=True)
    _state['thread'] = t
    t.start()
    protocol.send(f'[+] Stream started (interval={interval_sec}s)')
    return t


def stop_stream():
    with _state['lock']:
        _state['running'] = False
    return _state['count']


def stream_status(protocol):
    with _state['lock']:
        running = _state['running']
        cnt = _state['count']
    protocol.send(f'[+] Stream: {"running" if running else "stopped"}, captures: {cnt}')
