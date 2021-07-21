from typing import Union, Dict, List

from telethon.events import NewMessage, CallbackQuery
from telethon.tl.custom import Message
from telethon import Button


FAMovie = Dict[str, Union[str, int, List[Union[str, Dict[str, str]]], None]]
MessageEvent = Union[NewMessage.Event, Message]
CallbackMessageEventLike = Union[CallbackQuery.Event, MessageEvent]
Keyboard = List[List[Button]]
