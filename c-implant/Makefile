# reverse-backdoor C-implant
# Cross-platform native agent (~15KB stripped)

CC_LINUX   ?= gcc
CC_WIN     ?= x86_64-w64-mingw32-gcc
CFLAGS     ?= -O2 -s -Wall -Wextra
LDFLAGS_LINUX = -lpthread
LDFLAGS_WIN   = -lws2_32

.PHONY: all linux windows clean

all: agent_linux agent.exe

agent_linux: agent.c
	$(CC_LINUX) $(CFLAGS) -o agent_linux agent.c $(LDFLAGS_LINUX)
	strip agent_linux
	@echo "[+] Linux agent built: agent_linux ($$(wc -c < agent_linux) bytes)"

agent.exe: agent.c
	$(CC_WIN) $(CFLAGS) -o agent.exe agent.c $(LDFLAGS_WIN)
	strip agent.exe 2>/dev/null || true
	@echo "[+] Windows agent built: agent.exe ($$(wc -c < agent.exe) bytes)"

linux: agent_linux
windows: agent.exe

clean:
	rm -f agent_linux agent.exe
