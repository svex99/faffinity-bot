from typing import List

from telethon import Button

from bot_types import FAMovie, Keyboard


hide = [Button.inline('❌ Ocultar', b'delete')]


def search_result(result: FAMovie) -> Keyboard: 
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

    buttons.append(hide)

    return buttons


def movie_keyboard(mid: str) -> Keyboard:
    """
    Keyboard for see movie synposis, awards and reviews.
    """
    mid = mid.encode('utf8')

    return [
        [
            Button.inline('ℹ Sinopsis', b'synopsis_' + mid)
        ], [
            Button.inline('🏆 Premios', b'awards_' + mid),
            Button.inline('💭 Críticas', b'reviews_' + mid),
        ],
        hide
    ]