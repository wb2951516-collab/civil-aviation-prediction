"""单实例与窗口唤醒工具（Windows 原生 API，无第三方依赖）

提供：
- acquire_single_instance_mutex: 命名互斥量单实例保护（返回是否为首个实例）
- acquire_single_instance_mutex_handle: 同上，返回句柄供退出时 CloseHandle 释放
- create_wakeup_event / signal_wakeup_event / poll_wakeup_event:
  命名事件唤醒通道——新启动实例通知已运行实例恢复窗口（支持隐藏窗口场景）
- find_window_by_title / restore_and_foreground:
  枚举顶层窗口（含隐藏）按标题匹配并恢复前置
"""

import ctypes
from ctypes import wintypes

_MUTEX_NAME = "CAPM_PASSENGER_FORECAST_SINGLE_INSTANCE"
_EVENT_NAME = "CAPM_PASSENGER_FORECAST_WAKEUP_EVENT"

ERROR_ALREADY_EXISTS = 183
SW_RESTORE = 9
WAIT_OBJECT_0 = 0


def _kernel32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateMutexW.restype = wintypes.HANDLE
    k.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateEventW.restype = wintypes.HANDLE
    k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenEventW.restype = wintypes.HANDLE
    k.SetEvent.argtypes = [wintypes.HANDLE]
    k.SetEvent.restype = wintypes.BOOL
    k.ResetEvent.argtypes = [wintypes.HANDLE]
    k.ResetEvent.restype = wintypes.BOOL
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.WaitForSingleObject.restype = wintypes.DWORD
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    k.GetLastError.argtypes = []
    k.GetLastError.restype = wintypes.DWORD
    return k


def acquire_single_instance_mutex(name: str = _MUTEX_NAME) -> bool:
    """尝试获取单实例互斥量。返回 True 表示当前是首个实例。"""
    k = _kernel32()
    handle = k.CreateMutexW(None, False, name)
    if not handle:
        return True
    last_error = k.GetLastError()
    if last_error == ERROR_ALREADY_EXISTS:
        return False
    return True


def acquire_single_instance_mutex_handle(name: str = _MUTEX_NAME):
    """获取互斥量句柄（返回 handle），供退出时 CloseHandle 显式释放。"""
    k = _kernel32()
    handle = k.CreateMutexW(None, False, name)
    if not handle:
        return None
    return handle


def release_mutex_handle(handle) -> None:
    if handle:
        try:
            _kernel32().CloseHandle(handle)
        except Exception:
            pass


def create_wakeup_event(name: str = _EVENT_NAME):
    """创建/打开命名唤醒事件（手动重置）。"""
    k = _kernel32()
    event = k.CreateEventW(None, True, False, name)  # manual-reset, 初始未触发
    if not event:
        event = k.OpenEventW(0x001F0003, False, name)  # EVENT_ALL_ACCESS
    return event


def signal_wakeup_event(name: str = _EVENT_NAME) -> bool:
    """由新启动实例调用：通知已有实例恢复窗口。"""
    k = _kernel32()
    try:
        event = k.OpenEventW(0x001F0003, False, name)
        if not event:
            return False
        k.SetEvent(event)
        k.CloseHandle(event)
        return True
    except Exception:
        return False


def poll_wakeup_event(event_handle) -> bool:
    """非阻塞检查唤醒事件是否已触发；触发后自动复位。"""
    if not event_handle:
        return False
    try:
        k = _kernel32()
        result = k.WaitForSingleObject(event_handle, 0)
        if result == WAIT_OBJECT_0:
            k.ResetEvent(event_handle)
            return True
    except Exception:
        pass
    return False


def _enum_window_titles() -> list:
    """枚举所有顶层窗口（含隐藏），返回 [(hwnd, title)]。"""
    k = _kernel32()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    results = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, lparam):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        if title:
            results.append((hwnd, title))
        return True

    user32.EnumWindows(_cb, 0)
    return results


def find_window_by_title(title: str):
    """按标题查找顶层窗口（含隐藏窗口）。返回 hwnd 或 None。"""
    for hwnd, t in _enum_window_titles():
        if t == title or (t and title in t):
            return hwnd
    return None


def restore_and_foreground(hwnd) -> bool:
    """恢复窗口（含从最小化/隐藏状态）并置于前台。"""
    if not hwnd:
        return False
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.ShowWindow.argtypes = [wintypes.HWND, wintypes.INT]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False
