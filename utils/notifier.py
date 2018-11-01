import threading
from os import path
from time import sleep
from pkg_resources import Requirement
from pkg_resources import resource_filename
from win32api import GetModuleHandle, PostQuitMessage
from win32con import (
    CW_USEDEFAULT, IDI_APPLICATION, IMAGE_ICON, LR_DEFAULTSIZE,
    LR_LOADFROMFILE, WM_DESTROY, WM_USER, WS_OVERLAPPED, WS_SYSMENU
)
from win32gui import (
    CreateWindow, DestroyWindow, LoadIcon, LoadImage, NIF_ICON, NIF_INFO,
    NIF_MESSAGE, NIF_TIP, NIM_ADD, NIM_DELETE, NIM_MODIFY, RegisterClass,
    UnregisterClass, Shell_NotifyIcon, UpdateWindow, WNDCLASS
)

from typing import Optional


class Notifier:
    def __init__(self):
        self._thread = None

    def _notify(self,
                title: str,
                msg: str,
                icon_path: str,
                duration: int) -> None:
        message_map = {WM_DESTROY: self.on_destroy}

        # Register the window class.
        self.wc = WNDCLASS()
        self.hinst = self.wc.hInstance = GetModuleHandle(None)
        self.wc.lpszClassName = str("PythonTaskbar")  # must be a string
        self.wc.lpfnWndProc = message_map  # could also specify a wndproc.
        try:
            self.classAtom = RegisterClass(self.wc)
        except Exception:
            pass #not sure of this  TODO fuck me
        style = WS_OVERLAPPED | WS_SYSMENU
        self.hwnd = CreateWindow(self.classAtom, "Taskbar", style,
                                 0, 0, CW_USEDEFAULT,
                                 CW_USEDEFAULT,
                                 0, 0, self.hinst, None)
        UpdateWindow(self.hwnd)

        # icon
        if icon_path is not None:
            icon_path = path.realpath(icon_path)
        else:
            icon_path = resource_filename(Requirement.parse("win10toast"), "win10toast/data/python.ico")
        icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
        try:
            hicon = LoadImage(self.hinst, icon_path,
                              IMAGE_ICON, 0, 0, icon_flags)
        except Exception:  # TODO handle specific exception
            hicon = LoadIcon(0, IDI_APPLICATION)

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, WM_USER + 20, hicon, "Tooltip")
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO,
                                      WM_USER + 20,
                                      hicon, "Balloon Tooltip", msg, 200,
                                      title))
        # take a rest then destroy
        sleep(duration)
        DestroyWindow(self.hwnd)
        UnregisterClass(self.wc.lpszClassName, None)

    def is_notification_active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def on_destroy(self, hwnd, msg, wparam, lparam) -> None:
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0)

    def notify(self,
               title: str,
               msg: str,
               icon_path: Optional[str]=None,
               duration: int=5,
               threaded: bool=False) -> bool:
        if not threaded:
            self._notify(title, msg, icon_path, duration)
        else:
            if self.is_notification_active():
                return False

            self._thread = threading.Thread(target=self._notify, args=(title, msg, icon_path, duration))
            self._thread.start()
        return True
