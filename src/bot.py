import os
import logging
import asyncio
import urllib3
from functools import partial
from datetime import datetime

import dotenv
from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, StopPropagation
from python_filmaffinity import FilmAffinity
from python_filmaffinity.exceptions import FilmAffinityConnectionError
from redis import Redis
from requests_cache import CachedSession, RedisCache

import keyboards as kbs
import messages as msgs
from bot_types import MessageEvent, CallbackMessageEventLike
from utils import humanize


dotenv.load_dotenv()
urllib3.disable_warnings()
logging.basicConfig(
    format='[%(levelname)s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)

API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
REDIS_HOST = os.environ['REDIS_HOST']

bot = TelegramClient('files/faffinity-bot', API_ID, API_HASH)
bot.start(bot_token=BOT_TOKEN)

cache_session = CachedSession(backend=RedisCache(connection=Redis(REDIS_HOST)))
fa = FilmAffinity(cache_backend='redis')
fa.session = cache_session


@bot.on(NewMessage(pattern='/start'))
async def start_handler(event: MessageEvent):
    """
    /start command handler.
    """
    await event.respond(msgs.start_command)

    raise StopPropagation


@bot.on(NewMessage(pattern='/help'))
async def start_handler(event: MessageEvent):
    """
    /help command handler.
    """
    await event.respond(msgs.help_command)

    raise StopPropagation


@bot.on(NewMessage(pattern='/support'))
async def start_handler(event: MessageEvent):
    """
    /support command handler.
    """
    await event.respond(msgs.support_command)

    raise StopPropagation


@bot.on(CallbackQuery(pattern=b'delete'))
async def delete_handler(event: CallbackQuery.Event):
    """
    Deletes the message of the button clicked.
    """
    await event.delete()

    raise StopPropagation


@bot.on(NewMessage(pattern=r'(?P<title>[^/].*)'))
@bot.on(NewMessage(pattern=r'/cast (?P<cast>.+)'))
@bot.on(NewMessage(pattern=r'/director (?P<director>.+)'))
async def search_handler(event: MessageEvent):
    """
    Handles queries by title, cast and director.
    """
    query = event.pattern_match.groupdict()

    try:
        result = await bot.loop.run_in_executor(
            None, partial(fa.search, 20, **query)
        )
    except FilmAffinityConnectionError as e:
        await event.respond(msgs.fa_error)
        logging.error(e)
    else:
        if result:
            await event.respond(
                message='✅ Resultados de la búsqueda.',
                buttons=kbs.search_result(result)
            )
        else:
            await event.respond('⚠️ No se han encontrado coincidencias.')

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'film_(?P<id>\d+)'))
async def movie_handler(event: CallbackMessageEventLike):
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(msgs.fa_error)
        logging.error(e)
    else:
        poster = movie['poster'] if movie['poster'] else 'files/noimgfull.jpg'
        humanize(movie)
        await event.respond(
            message=msgs.movie_template.format(**movie),
            file=poster,
            buttons=kbs.movie_keyboard(movie['id'])
        )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'synopsis_(?P<id>\d+)'))
async def synopsis_handler(event: CallbackQuery.Event):
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(msgs.fa_error)
        logging.error(e)
    else:
        await event.respond(
            message=msgs.movie_synopsis.format(**movie),
            buttons=kbs.hide
        )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'awards_(?P<id>\d+)'))
async def awards_handler(event: CallbackQuery.Event):
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(msgs.fa_error)
        logging.error(e)
    else:
        awards = movie['awards']
        if awards:
            awards_text = f'🏆 **Premios: {movie["title"]}** 🏆\n\n'
            final = ''

            for a in awards:
                if a['year'].isalnum():
                    awards_text += f'🔸 `{a["year"]}`: {a["award"]}\n'
                else:
                    final = f'{a["year"]} ↗️'

            awards_text += (
                f'\n[{final if final else "Ver en FilmAffinity↗️"}]'
                f'(https://www.filmaffinity.com/es/film{movie["id"]}.html)'
            )

            await event.respond(
                message=awards_text,
                buttons=kbs.hide,
                link_preview=False
            )
        else:
            await event.respond('⚠️ No hay premios para mostrar.')


@bot.on(CallbackQuery(pattern=rb'reviews_(?P<id>\d+)'))
async def reviews_handler(event: CallbackQuery.Event):
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(msgs.fa_error)
        logging.error(e)
    else:
        reviews = movie['reviews']
        if reviews:
            reviews_text = (
                f'💭 **Críticas: {movie["title"]}** 💭\n'
            )

            for r in reviews:
                # remove `[` and `]` for don't break telegram markdown
                actual_review = r['review'].replace('[', '')
                actual_review = actual_review.replace(']', '')
                reviews_text += (
                    f'\n👤 **{r["author"]}** [enlace↗️]'
                    f'({r["url"] if r["url"] else f"www.filmaffinity.com/es/film{mid}.html"})\n'
                    f'💭 __{actual_review}__\n'
                )

            reviews_text += f'\n[Ver en FilmAffinity↗️](www.filmaffinity.com/es/pro-reviews.php?movie-id={mid})'

            await event.respond(
                message=reviews_text,
                buttons=kbs.hide,
                link_preview=False
            )
        else:
            await event.respond('⚠️ No hay crítica para mostrar.')


# #################### admin handlers ####################
@bot.on(NewMessage())
async def admin_handler(event: MessageEvent):
    """
    Raises StopPropagation if event's user is not the admin.
    """
    if event.sender_id != ADMIN_ID:
        raise StopPropagation


@bot.on(NewMessage(pattern='/session'))
async def session_handler(event: MessageEvent):
    """
    /session command handler.
    Returns the bot session file.
    """
    format_ = "%Y-%m-%d %H:%M:%S %Z%z"
    await event.respond(
        message=f'`{datetime.now().strftime(format_)}`',
        file='files/faffinity-bot.session'
    )

    raise StopPropagation


async def main():
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
