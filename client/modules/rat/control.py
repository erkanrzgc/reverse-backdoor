import subprocess


def inject_keystroke(keys):
    """Simulate keystrokes on the target machine."""
    try:
        import pyautogui
        pyautogui.typewrite(keys, interval=0.05)
        return f'[+] Injected keystrokes: {keys[:20]}...' if len(keys) > 20 else f'[+] Injected keystrokes: {keys}'
    except Exception:
        return '[-] Keystroke injection requires pyautogui'


def move_mouse(x, y):
    """Move mouse to specific coordinates."""
    try:
        import pyautogui
        pyautogui.moveTo(x, y)
        return f'[+] Mouse moved to ({x}, {y})'
    except Exception:
        return '[-] Mouse movement requires pyautogui'


def click_mouse(button='left'):
    """Click mouse button."""
    try:
        import pyautogui
        pyautogui.click(button=button)
        return f'[+] Mouse {button} click'
    except Exception:
        return '[-] Mouse click requires pyautogui'


def lock_screen():
    """Lock the target machine's screen."""
    import os
    if os.name == 'nt':
        subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True)
    else:
        subprocess.run('loginctl lock-session', shell=True)
    return '[+] Screen locked'
