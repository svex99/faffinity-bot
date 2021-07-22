from typing import List, Callable

from telethon import Button

from bot_types import FAMovie, Keyboard


def hide(_: Callable):
    return [Button.inline(f'❌ {_("Hide")}', b'delete')]


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
    # for i in range(0, len(result), 2):
    #     buttons.append(
    #         [
    #             Button.inline(
    #                 result[i]['title'],
    #                 b'film_' + result[i]['id'].encode('utf8')
    #             ),
    #             Button.inline(
    #                 result[i + 1]['title'],
    #                 b'film_' + result[i + 1]['id'].encode('utf8')
    #             ),
    #         ]
    #     )

    # if len(result) % 2 == 1:
    #     buttons.append(
    #         [
    #             Button.inline(
    #                 result[-1]['title'],
    #                 b'film_' + result[-1]['id'].encode('utf8')
    #             ),
    #         ]
    #     )

    buttons.append(hide(_))

    return buttons


def movie_keyboard(_: Callable, mid: str) -> Keyboard:
    """
    Keyboard for see movie synopsis, awards and reviews.
    """
    mid = mid.encode('utf8')

    return [
        [
            Button.inline(f'ℹ {_("Synopsis")}', b'synopsis_' + mid)
        ], [
            Button.inline(f'🏆 {_("Awards")}', b'awards_' + mid),
            Button.inline(f'💭 {_("Reviews")}', b'reviews_' + mid),
        ],
        hide(_)
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
