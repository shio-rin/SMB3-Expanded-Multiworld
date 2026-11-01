# SPDX-License-Identifier: MPL-2.0
"""launcher / windows implementation for managed SMB3X sessions."""
from pathlib import Path
import logging, os, subprocess
from ..shared.resources import RESOURCE_ROOT as ROOT
from ..shared.serialization import read

def association_executable(association):
    """Read the Shell's open target, including a Windows per-user default."""
    import ctypes
    from ctypes import wintypes
    query = ctypes.WinDLL('Shlwapi').AssocQueryStringW
    query.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    query.restype = ctypes.c_long
    value = ctypes.create_unicode_buffer(32768)
    size = wintypes.DWORD(len(value))
    result = query(0, 2, association, 'open', value, ctypes.byref(size))
    return Path(value.value) if result == 0 and value.value else None

def register_association(launcher):
    """Optional current-user convenience; existing defaults are never replaced."""
    import winreg
    prefix = 'Software\\Classes'
    extension = '.apsmb3x'
    progid = 'Archipelago.SMB3X.Player'
    launcher = Path(launcher).resolve()

    def value(root, path, name=''):
        try:
            with winreg.OpenKey(root, path) as key:
                return winreg.QueryValueEx(key, name)[0]
        except FileNotFoundError:
            return None

    def existing():
        return value(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\.apsmb3x\\UserChoice', 'ProgId') or value(winreg.HKEY_CLASSES_ROOT, extension)

    def preserve(association):
        target = association_executable(association)
        if target is not None and target.is_file() and (target.resolve() == launcher):
            return 'already-current'
        logging.getLogger('SMB3X').warning("Optional .apsmb3x association left unchanged (open target: %s). This selected player will continue through this Launcher. Double-click may use another application; use this installation's Open Patch.", str(target) if target else 'unresolved or missing')
        return 'preserved'
    if existing():
        return preserve(extension)
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid):
            occupied = True
    except FileNotFoundError:
        occupied = False
    if occupied:
        if preserve(progid) != 'already-current':
            return 'preserved'
    else:
        values = {progid: 'Archipelago SMB3X Player', progid + '\\shell\\open\\command': '"' + str(launcher) + '" "%1"', progid + '\\DefaultIcon': str(launcher) + ',0'}
        for path, data in values.items():
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, prefix + '\\' + path) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, data)
    if existing():
        return preserve(extension)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, prefix + '\\' + extension) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, progid)
    import ctypes
    ctypes.windll.shell32.SHChangeNotify(134217728, 0, None, None)
    return 'registered'

def optional_association(launcher):
    """Only expected Windows/registry failures are nonfatal to explicit opening."""
    try:
        return register_association(launcher)
    except OSError as exc:
        logging.getLogger('SMB3X').warning('Optional .apsmb3x registration unavailable: %s. Continuing this selected player through Launcher. Use Open Patch if double-click opens another application.', exc)
        return 'unavailable'

def process_identity(pid):
    """PID reuse cannot turn an old ownership record into authority over a process."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(4096, False, int(pid))
    if not handle:
        return None
    try:
        created, exited, kern, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, *map(ctypes.byref, (created, exited, kern, user))):
            return None
        if exited.dwHighDateTime or exited.dwLowDateTime:
            return None
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return None
        return dict(pid=int(pid), created=created.dwHighDateTime << 32 | created.dwLowDateTime, exe=buffer.value.casefold())
    finally:
        kernel.CloseHandle(handle)

def close_owned_emulator(process, timeout=8):
    """Request normal shutdown/SaveConfig, then bound only this Popen's wait."""
    if process.poll() is not None:
        return True
    if os.name == 'nt':
        expected = process_identity(process.pid)
        import ctypes
        from ctypes import wintypes
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetWindow.restype = wintypes.HWND
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.EnumWindows.argtypes = [callback, wintypes.LPARAM]

        @callback
        def visit(hwnd, param):
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            title = ctypes.create_unicode_buffer(1024)
            user.GetWindowTextW(hwnd, title, 1024)
            if pid.value == process.pid and (not user.GetWindow(hwnd, 4)) and ('BizHawk' in title.value) and (process.poll() is None) and expected and (process_identity(process.pid) == expected):
                user.PostMessageW(hwnd, 16, 0, 0)
            return True
        user.EnumWindows(visit, 0)
        try:
            process.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            pass
    logging.getLogger('SMB3X').warning('Saved game is safe; normal emulator close timed out. Latest unsaved emulator preferences may not have been written.')
    process.terminate()
    process.wait(timeout=10)
    return False

def retire_orphan(root, key, close=False):
    """Only a proven emulator from this session whose backend is gone may close."""
    path = root / 'owner.json'
    if not path.exists():
        return
    owner = read(path)
    if owner.get('schema') != 2 or owner.get('session_key') != key:
        raise ValueError('Session process-ownership metadata is invalid; no process was closed')
    previous = owner.get('emulator')
    if not previous or process_identity(previous['pid']) != previous:
        return
    backend = owner.get('backend')
    if backend and process_identity(backend['pid']) == backend:
        raise ValueError('This session still has an open client/error dialog. Close it normally before reopening the player file.')
    if not close:
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(1, False, previous['pid'])
    if not handle:
        raise ValueError('The previous owned emulator is still open; close it normally and reopen this player file')
    try:
        if process_identity(previous['pid']) == previous:
            if not kernel.TerminateProcess(handle, 0):
                raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)

def protect(data, unprotect=False):
    """Windows user-bound credential storage; no password enters the player file."""
    if not data:
        return ''
    import ctypes, base64
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    raw = base64.b64decode(data) if unprotect else data.encode()
    buffer = ctypes.create_string_buffer(raw)
    src = Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    out = Blob()
    fn = ctypes.windll.crypt32.CryptUnprotectData if unprotect else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(src), None, None, None, None, 1, ctypes.byref(out)):
        raise ctypes.WinError()
    try:
        result = ctypes.string_at(out.data, out.size)
        return result.decode() if unprotect else base64.b64encode(result).decode()
    finally:
        ctypes.windll.kernel32.LocalFree(out.data)
