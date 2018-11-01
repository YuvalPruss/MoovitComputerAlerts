from typing import NamedTuple

from utils.notifier import Notifier

Alert = NamedTuple('Alert', [('title', str), ('message', str)])


class MessageManager:
    DEFAULT_ICON_PATH = 'images/moovit.ico'

    def __init__(self) -> None:
        self.notifier = Notifier()

    def show_message(self,
                     title: str,
                     message: str,
                     duration: int=5,
                     icon_path: str=DEFAULT_ICON_PATH) -> None:
        self.notifier.notify(title, message, icon_path, duration)
