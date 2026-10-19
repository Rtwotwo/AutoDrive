"""Window activation for this application's Windows single-instance launcher."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import time

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel.CreateMutexW.restype = wintypes.HANDLE
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel.WaitForSingleObject.restype = wintypes.DWORD
kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]


def claim_instance_mutex(name='Local\\AutoDrivePaperStudioDesktop'):
    """Hold ownership, not mere existence: a stale unowned object is reusable."""
    handle = kernel.CreateMutexW(None, False, name)
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    result = kernel.WaitForSingleObject(handle, 0)
    if result in (0, 0x80): return handle  # acquired or abandoned by an exited owner
    error = ctypes.get_last_error()
    kernel.CloseHandle(handle)
    if result == 0x102: return None  # another running instance owns it
    raise ctypes.WinError(error)


def release_instance_mutex(handle):
    if handle:
        kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)

user = ctypes.WinDLL('user32', use_last_error=True)
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
user.EnumWindows.restype = wintypes.BOOL
user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user.GetWindowTextW.restype = ctypes.c_int
for name in ('IsWindow', 'IsWindowVisible', 'IsIconic', 'SetForegroundWindow', 'BringWindowToTop'):
    getattr(user, name).argtypes = [wintypes.HWND]
    getattr(user, name).restype = wintypes.BOOL
user.GetForegroundWindow.restype = wintypes.HWND
user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user.ShowWindow.restype = wintypes.BOOL
user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user.PostMessageW.restype = wintypes.BOOL


def main_window(pid):
    """Find only Paper Studio's top-level window in the stated process, including hidden windows."""
    matches = []
    @CALLBACK
    def visit(handle, _):
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid:
            title = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(handle, title, len(title))
            if title.value.startswith('Paper Studio ·'):
                matches.append(int(handle))
        return True
    user.EnumWindows(visit, 0)
    return matches[0] if matches else None


def window_state(handle):
    return {'visible': bool(handle and user.IsWindowVisible(handle)),
            'minimized': bool(handle and user.IsIconic(handle)),
            'foreground': bool(handle and user.GetForegroundWindow() == handle)}


def activate(handle):
    if not handle or not user.IsWindow(handle):
        return False
    # Explicit second ShowWindow defeats an inherited STARTUPINFO SW_HIDE on first display.
    user.ShowWindow(handle, 9 if user.IsIconic(handle) else 5)
    user.ShowWindow(handle, 5)
    user.BringWindowToTop(handle)
    user.SetForegroundWindow(handle)
    state = window_state(handle)
    return state['visible'] and not state['minimized']


def activate_existing(status_path, timeout=15):
    """Wait for the first launch to create its window, then reveal it without touching API/session data."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            status = json.loads(Path(status_path).read_text(encoding='utf-8'))
            handle = main_window(int(status['pid']))
            if activate(handle):
                return True
        except (OSError, ValueError, KeyError, TypeError):
            pass
        time.sleep(.1)
    return False
