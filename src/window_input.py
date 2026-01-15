import ctypes
import time
from ctypes import wintypes

# Windows API Constants
INPUT_KEYBOARD = 1
# Constants
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

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
    """
    Simulates pressing and releasing a key using Scan Codes.
    This is required for many DirectX games (Source Engine) that ignore VK codes.
    """
    user32 = ctypes.windll.user32
    
    # Map Virtual Key to Scan Code
    scan_code = user32.MapVirtualKeyW(vk_code, 0)
    
    # Press (Scan Code)
    inp_down = INPUT(type=INPUT_KEYBOARD,
                     ki=KEYBDINPUT(wVk=0, 
                                   wScan=scan_code, 
                                   dwFlags=KEYEVENTF_SCANCODE, 
                                   time=0, 
                                   dwExtraInfo=None))
    
    user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
    
    time.sleep(0.2) # Longer hold for source engine
    
    # Release (Scan Code)
    inp_up = INPUT(type=INPUT_KEYBOARD,
                   ki=KEYBDINPUT(wVk=0, 
                                 wScan=scan_code, 
                                 dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 
                                 time=0, 
                                 dwExtraInfo=None))
    
    user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

if __name__ == "__main__":
    print("Pressing F9 (0x78) in 2 seconds...")
    time.sleep(2)
    press_key(0x78)
    print("Pressed.")
