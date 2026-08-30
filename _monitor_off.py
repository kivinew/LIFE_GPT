import ctypes, sys
user32 = ctypes.windll.user32
HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
# 2 = turn off monitor
result = user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
print(f"Monitor off result: {result}", file=sys.stderr)