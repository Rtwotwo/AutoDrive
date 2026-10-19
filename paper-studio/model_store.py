"""Private model profiles encrypted for the current Windows user (DPAPI)."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import uuid


def crypt(data, decrypt=False):
    if os.name != 'nt':
        raise ValueError('加密保存模型配置需要 Windows；可取消勾选，仅在内存使用。')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    library = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    func = library.CryptUnprotectData if decrypt else library.CryptProtectData
    func.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                     ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    func.restype = wintypes.BOOL
    # UI_FORBIDDEN only: never use LOCAL_MACHINE, which shares decryption across users.
    if not func(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError('Windows 无法解密模型配置，请在此电脑重新填写。' if decrypt else 'Windows 加密失败；未保存配置。')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.memset(target.data, 0, target.size)
        kernel.LocalFree(target.data)
        ctypes.memset(buffer, 0, len(data))


class ModelStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > 1_000_000:
                raise ValueError()
            value = json.loads(crypt(self.path.read_bytes(), decrypt=True))
            if not isinstance(value, dict) or value.get('version') != 1:
                raise ValueError()
            return value
        except (ValueError, OSError):
            raise ValueError('已保存的模型配置无法读取；请重新填写并保存。原文件尚未覆盖。') from None

    def save(self, value):
        # Encryption happens before any file is created. No plaintext temporary file.
        encrypted = crypt(json.dumps(value, ensure_ascii=False).encode('utf-8'))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with temp.open('xb') as stream:
                stream.write(encrypted)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)

    def clear(self):
        self.path.unlink(missing_ok=True)
