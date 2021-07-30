from typing import List, Callable, Optional

from telethon import Button

from bot_types import FAMovie, Keyboard


def hide(
    _: Callable,
    linked_msg_ids: Optional[List[Optional[int]]] = None,
) -> Keyboard:
    """
    Builds the hide button that when clicked deletes the message binded,
    optionally can delete two messages more.
    """
    linked_msg_ids = linked_msg_ids or []
    data = b'delete'

    for msg_id in linked_msg_ids:
        if msg_id is None:
            continue

        data += (b'_' + str(msg_id).encode('utf8'))

    return [Button.inline(f'➖ {_("Hide")}', data)]


def search_result(_: Callable, result: List[FAMovie]) -> Keyboard:
    """
    Keyboard for results of a movie query.
    """
    buttons = [
        [
            Button.inline(
                movie['title'],
                b'film_' + movie['id'].encode('utf8')
            )
        ] for movie in result
    ]

    buttons.append(hide(_))

    return buttons


def movie_keyboard(
    _: Callable,
    mid: str,
    linked_msg_ids: Optional[List[Optional[int]]] = None
) -> Keyboard:
    """
    Keyboard for see movie synopsis, awards and reviews.
    """
    mid = mid.encode('utf8')

    return [
        [
            Button.inline(f'🖼 {_("Images")}', b'images_' + mid),
            Button.inline(f'ℹ {_("Synopsis")}', b'synopsis_' + mid)
        ], [
            Button.inline(f'🏆 {_("Awards")}', b'awards_' + mid),
            Button.inline(f'💭 {_("Reviews")}', b'reviews_' + mid),
        ],
        hide(_, linked_msg_ids)
    ]


def select_lang() -> Keyboard:
    """
    Select language keyboard.
    """
    return [
        [
            Button.inline('🇪🇸 Español', b'lang_es'),
            Button.inline('🇬🇧 English', b'lang_en')
        ]
    ]


def tops(_: Callable) -> Keyboard:
    return [
        [
            Button.inline('🔸 HBO', b'top_HBO'),
            Button.inline('🔸 Netflix', b'top_Netflix'),
            Button.inline('🔸 Filmin', b'top_Filmin')
        ], [
            Button.inline('🔸 Movistar', b'top_Movistar'),
            Button.inline('🔸 Rakuten', b'top_Rakuten')
        ],
        hide(_)
    ]


def inline_details(_: Callable, mid: str) -> Keyboard:
    return [
        Button.url(_('see_at_bot'), f'https://t.me/faffinitybot?start=id_{mid}')
    ]


def support(_: Callable):
    return [
        [
            Button.url(_('rate'), 'https://t.me/BotsArchive/2091'),
        ],
        hide(_)
    ]
