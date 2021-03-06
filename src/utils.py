from typing import List, Callable
from logging import StreamHandler
import asyncio
import random

from telethon import TelegramClient

from bot_types import FAMovie


def humanize(data: FAMovie):
    """
    Humanize the movie data, modifies the data inplace.
    """
    for key in data:
        if data[key]:
            if isinstance(data[key], list):
                if isinstance(data[key][0], (str, int,)):
                    # avoid repeated values in list
                    clean_list = []
                    for entry in data[key]:
                        if entry not in clean_list:
                            clean_list.append(entry)

                    data[key] = ", ".join(entry for entry in clean_list)
        else:
            data[key] = "`-`"

    return data


def get_random_ad(_: Callable, ads: List[str]) -> str:
    """
    Returns text of a random ad from files/ads.json or the default ad text.
    """
    return "\n\n" + (random.choice(ads) or _("default_ad"))


class TelegramLogsHandler(StreamHandler):
    """
    logging Handler to send logs to Telegram chat.
    """

    def __init__(self, client: TelegramClient, user_id: int):
        StreamHandler.__init__(self)
        self.client = client
        self.user_id = user_id

    async def _emit(self, message):
        try:
            await self.client.send_message(self.user_id, message)
        except ConnectionError:
            pass

    def emit(self, record):
        message = f"`{self.format(record)}`"
        try:
            asyncio.get_event_loop().create_task(self._emit(message))
        except RuntimeError:
            pass
