import os
import socket
import platform as pf


def get_sysinfo(platform):
    info_list = []
    try:
        uname = pf.uname()
        info_list.append(f"Operating System: {uname.system} {uname.release}")
        info_list.append(f"Version: {uname.version}")
        info_list.append(f"Machine: {uname.machine}")
        info_list.append(f"Node Name: {uname.node}")
        info_list.append(f"User: {platform.get_system_user()}")
        info_list.append(f"Processor: {uname.processor}")

        try:
            info_list.append(f"CPU Cores: {os.cpu_count()}")
        except Exception:
            pass

        mem_info = platform.get_memory_info()
        if mem_info:
            info_list.append(mem_info)

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            info_list.append(f"Local IP: {local_ip}")
        except Exception:
            pass

    except Exception as e:
        info_list.append(f"Error gathering info: {str(e)}")

    return "\n".join(info_list)
