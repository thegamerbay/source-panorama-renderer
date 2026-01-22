import ctypes
import time
from ctypes import wintypes

# Windows API Constants
# Windows API Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# Structures for SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("u", INPUT_UNION)]
    _anonymous_ = ("u",)

def press_key(vk_code):
    """Simulates pressing and releasing a key using Scan Codes."""
    user32 = ctypes.windll.user32
    scan_code = user32.MapVirtualKeyW(vk_code, 0)
    
    # Press
    inp_down = INPUT(type=INPUT_KEYBOARD,
                     ki=KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=None))
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
    
    time.sleep(0.1) 
    
    # Release
    inp_up = INPUT(type=INPUT_KEYBOARD,
                   ki=KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None))
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

def click_mouse():
    """Simulates a left mouse click to focus the window."""
    user32 = ctypes.windll.user32
    
    # Down
    inp_down = INPUT(type=INPUT_MOUSE,
                     mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTDOWN, time=0, dwExtraInfo=None))
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
    
    time.sleep(0.05)
    
    # Up
    inp_up = INPUT(type=INPUT_MOUSE,
                   mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=MOUSEEVENTF_LEFTUP, time=0, dwExtraInfo=None))
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

if __name__ == "__main__":
    print("Clicking in 2 seconds...")
    time.sleep(2)
    click_mouse()
