import base64
from server.ui.prompt import print_colored


def upload_file(protocol, file_name):
    try:
        with open(file_name, 'rb') as f:
            protocol.send(base64.b64encode(f.read()).decode())
    except Exception as e:
        print_colored(f'[-] Error uploading file: {str(e)}', 'red')


def download_file(protocol, file_name):
    try:
        result = protocol.recv()
        if isinstance(result, str) and result.startswith('[-]'):
            print_colored(result, 'red')
            return
        with open(file_name, 'wb') as f:
            f.write(base64.b64decode(result))
        print_colored(f'[+] File saved: {file_name}', 'green')
    except Exception as e:
        print_colored(f'[-] Error downloading file: {str(e)}', 'red')
