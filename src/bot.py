import os
import logging
import asyncio
import urllib3
import json
from functools import partial
from datetime import datetime

import dotenv
from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, StopPropagation, \
    InlineQuery
from telethon.tl.types import InputWebDocument
from telethon.errors.rpcerrorlist import MediaCaptionTooLongError
from python_filmaffinity import FilmAffinity
from python_filmaffinity.exceptions import FilmAffinityConnectionError
from redis import Redis
from requests_cache import CachedSession, RedisCache

import keyboards as kbs
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
NO_IMAGE = 'https://www.filmaffinity.com/imgs/movies/noimgfull.jpg'

TRANSLATIONS = json.load(open('files/i18n_messages.json'))

bot = TelegramClient('files/faffinity-bot', API_ID, API_HASH)
bot.start(bot_token=BOT_TOKEN)

redis = Redis(REDIS_HOST)

# FA cache
cache_session = CachedSession(backend=RedisCache(connection=redis))
# Spanish FA client
fa_es = FilmAffinity(lang='es', cache_backend='redis')
fa_es.session = cache_session
# English FA client
fa_en = FilmAffinity(lang='en', cache_backend='redis')
fa_en.session = cache_session


@bot.on(CallbackQuery(pattern=b'delete'))
async def delete_handler(event: CallbackQuery.Event):
    """
    Deletes the message of the button clicked.
    """
    await event.delete()

    raise StopPropagation


@bot.on(NewMessage())
@bot.on(CallbackQuery())
@bot.on(InlineQuery())
async def i18n_handler(event: CallbackMessageEventLike):
    """
    Sets the default language for this event.
    """
    lang = await bot.loop.run_in_executor(
        None, partial(redis.get, f'lang-{event.sender_id}')
    )

    if lang is None:
        lang = 'es'
        await bot.loop.run_in_executor(
            None, partial(redis.set, f'lang-{event.sender_id}', lang)
        )
    else:
        lang = lang.decode('utf8')

    event.lang = lang
    event.i18n = lambda key: TRANSLATIONS[key][lang]
    if lang == 'es':
        event.fa_client = fa_es
    else:
        event.fa_client = fa_en


@bot.on(InlineQuery())
async def inline_search_handler(event: InlineQuery.Event):
    _ = event.i18n
    fa = event.fa_client
    builder = event.builder

    try:
        result = await bot.loop.run_in_executor(
            None, partial(fa.search, 20, title=event.text)
        )
    except FilmAffinityConnectionError as e:
        await event.answer([
            builder.article(
                title=_('fa_error'),
                text=_('fa_error')
            )
        ])
        logging.error(e)
    else:
        if result:
            await event.answer([
                builder.article(
                    title=movie['title'],
                    text=_('inline_result').format(**humanize(movie)),
                    thumb=InputWebDocument(
                        url=movie['poster'],
                        size=1,
                        mime_type='image/jpg',
                        attributes=[]
                    ) if movie['poster'] != '/imgs/movies/noimgfull.jpg' else None,
                    link_preview=False,
                    buttons=kbs.inline_details(_, movie['id'])
                )
                for movie in result
            ])
        else:
            await event.answer([
                builder.article(
                    title=_('no_matches').format(query=event.text),
                    text=_('no_matches').format(query=event.text),
                )
            ])


@bot.on(NewMessage(pattern=r'/start( id_(?P<id>\d+))?'))
async def start_handler(event: MessageEvent):
    """
    /start command handler.
    """
    _ = event.i18n
    mid = event.pattern_match['id']

    if not mid:
        await event.respond(_('start'))

        raise StopPropagation


@bot.on(NewMessage(pattern='/help'))
async def help_handler(event: MessageEvent):
    """
    /help command handler.
    """
    _ = event.i18n

    admin_help = (
        '\n\n##### Admin help #####\n'
        '/session - get the session file.\n'
        '/broadcast - broadcast a message to users of the bot.\n'
        '/stats - stats of the bot.'
    ) if event.sender_id == ADMIN_ID else ''

    await event.respond(
        message=_('help') + admin_help,
        buttons=kbs.hide(_)
    )

    raise StopPropagation


@bot.on(NewMessage(pattern='/support'))
async def support_handler(event: MessageEvent):
    """
    /support command handler.
    """
    _ = event.i18n

    await event.respond(
        message=_('support'),
        buttons=kbs.hide(_),
        link_preview=False
    )

    raise StopPropagation


@bot.on(NewMessage(pattern=r'(?P<title>[^/].*)'))
@bot.on(NewMessage(pattern=r'/cast (?P<cast>.+)'))
@bot.on(NewMessage(pattern=r'/director (?P<director>.+)'))
async def search_handler(event: MessageEvent):
    """
    Handles queries by title, cast and director.
    """
    _ = event.i18n
    fa = event.fa_client
    query = event.pattern_match.groupdict()

    try:
        result = await bot.loop.run_in_executor(
            None, partial(fa.search, 20, **query)
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        if result:
            await event.respond(
                message=_('query_results'),
                buttons=kbs.search_result(_, result)
            )
        else:
            await event.respond(
                message=_('no_matches').format(
                    query=(
                        query.get('title') or
                        query.get('cast') or
                        query.get('director') or
                        '`-`'
                    )
                )
            )

    raise StopPropagation


@bot.on(NewMessage(pattern=r'/start id_(?P<id>\d+)'))
@bot.on(CallbackQuery(pattern=rb'film_(?P<id>\d+)'))
async def movie_handler(event: CallbackMessageEventLike):
    """
    Shows the details about an specific movie.

    The movie id can be received from a click in an inline button or a link
    to the bot with the parameter start properly setted.
    """
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match['id']
    if isinstance(mid, bytes):
        mid = mid.decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        poster = movie['poster'] or NO_IMAGE
        humanize(movie)

        try:
            await event.respond(
                message=_('movie_template').format(**movie),
                file=poster,
                buttons=kbs.movie_keyboard(_, movie['id'])
            )
        except MediaCaptionTooLongError:
            await event.respond(
                file=poster
            )
            await event.respond(
                message=_('movie_template').format(**movie),
                buttons=kbs.movie_keyboard(_, movie['id']),
                link_preview=False
            )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'synopsis_(?P<id>\d+)'))
async def synopsis_handler(event: CallbackQuery.Event):
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        await event.respond(
            message=(
                f'ℹ **{_("Synopsis")}: '
                '{title}** ℹ\n\n{description}'.format(**movie)
            ),
            buttons=kbs.hide(_)
        )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'awards_(?P<id>\d+)'))
async def awards_handler(event: CallbackQuery.Event):
    lang = event.lang
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        awards = movie['awards']
        if awards:
            awards_text = f'🏆 **{_("Awards")}: {movie["title"]}** 🏆\n\n'
            final = ''

            for a in awards:
                if a['year'].isalnum():
                    awards_text += f'🔸 `{a["year"]}`: {a["award"]}\n'
                else:
                    final = f'↗ {a["year"]}'

            awards_text += (
                f'\n[{final if final else _("see_at_fa")}]'
                f'(https://www.filmaffinity.com/{lang}/film{movie["id"]}.html)'
            )

            await event.respond(
                message=awards_text,
                buttons=kbs.hide(_),
                link_preview=False
            )
        else:
            await event.respond(_('no_awards'))

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'reviews_(?P<id>\d+)'))
async def reviews_handler(event: CallbackQuery.Event):
    lang = event.lang
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        reviews = movie['reviews']
        if reviews:
            reviews_text = (
                f'💭 **{_("Reviews")}: {movie["title"]}** 💭\n'
            )

            for r in reviews:
                # remove `[` and `]` for don't break telegram markdown
                actual_review = r['review'].replace('[', '')
                actual_review = actual_review.replace(']', '')
                reviews_text += (
                    f'\n👤 [{r["author"]}]'
                    f'({r["url"] or f"www.filmaffinity.com/{lang}/film{mid}.html"})\n'
                    f'💭 __{actual_review}__\n'
                )

            reviews_text += (
                f'\n[{_("see_at_fa")}]'
                f'(www.filmaffinity.com/{lang}/pro-reviews.php?movie-id={mid})'
            )

            await event.respond(
                message=reviews_text,
                buttons=kbs.hide(_),
                link_preview=False
            )
        else:
            await event.respond(_('no_reviews'))

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'images_(?P<id>\d+)'))
async def reviews_handler(event: CallbackQuery.Event):
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match['id'].decode('utf8')

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{'id': mid, 'images': True})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        images = [
            still['image'] for still in movie['images']['stills']
            if still['image']
        ]
        if images:
            await event.respond(
                file=images
            )
        else:
            await event.respond(_('no_images'))

    raise StopPropagation


@bot.on(NewMessage(pattern='/language'))
async def language_handler(event: MessageEvent):
    """
    Sends a keyboard for language configuration.
    """
    await event.respond(
        message=TRANSLATIONS['select_lang']['es'],
        buttons=kbs.select_lang()
    )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=b'lang_(?P<lang>es|en)'))
async def select_language_handler(event: MessageEvent):
    """
    Handles the language selection by the user.
    """
    lang = event.pattern_match['lang'].decode('utf8')

    await bot.loop.run_in_executor(
        None, partial(redis.set, f'lang-{event.sender_id}', lang)
    )

    await event.edit(
        text=TRANSLATIONS['lang_selected'][lang]
    )

    raise StopPropagation


@bot.on(NewMessage(pattern='/top'))
async def top_handler(event: MessageEvent):
    """
    /top command handler.
    """
    _ = event.i18n

    await event.respond(
        message=_('select_top'),
        buttons=kbs.tops(_)
    )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb'top_(?P<service>\w+)'))
async def select_language_handler(event: MessageEvent):
    """
    Handles the top selection by the user.
    """
    _ = event.i18n
    fa: FilmAffinity = event.fa_client
    service = event.pattern_match['service'].decode('utf8')

    top_services = {
        'HBO': fa.top_hbo,
        'Netflix': fa.top_netflix,
        'Filmin': fa.top_filmin,
        'Movistar': fa.top_movistar,
        'Rakuten': fa.top_rakuten,
    }

    try:
        result = await bot.loop.run_in_executor(
            None, partial(top_services[service], 40)
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_('fa_error'))
        logging.error(e)
    else:
        text = f'🔝 Top {service} 🔝\n\n' + '\n\n'.join(
            [
                '`%2d.` ' % i + (
                    '[{title}](https://t.me/faffinitybot?start=id_{id})\n'
                    '📅 {year}      ⭐ {rating}/10'
                ).format(**movie)
                for movie, i in zip(result, range(1, 50))
            ]
        )
        await event.respond(
            message=text,
            buttons=kbs.hide(_),
            link_preview=False
        )

    raise StopPropagation


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


@bot.on(NewMessage(pattern=r'/broadcast'))
async def broadcast_handler(event: MessageEvent):
    """
    /broadcast command handler.
    """
    msg = await event.get_reply_message()

    if msg:
        # get the user ids from redis keys
        lang_keys = await bot.loop.run_in_executor(
            None, partial(redis.keys, 'lang-*')
        )
        user_ids = map(lambda x: int(x.split(b'-')[1]), lang_keys)

        await event.respond(f'📢 Starting broadcast to `{len(lang_keys)}` users...')

        # broadcast the message
        count = 0
        for user_id in user_ids:
            try:
                await bot.send_message(
                    entity=user_id,
                    message=msg
                )
            except Exception as e:
                if not isinstance(e, ValueError):
                    await event.respond(
                        message=(
                            f'`{type(e)}: {e}`\n\n'
                            f'Broadcasted to `{count}` users. Sleeping `60` seconds...`'
                        )
                    )
                    await asyncio.sleep(60)
            else:
                count += 1
                await asyncio.sleep(1)

        await event.reply(f'✅ Done. Broadcasted message to `{count}` users.')
    else:
        await event.respond('⚠ You must reply to a message with /broadcast command.')

    raise StopPropagation


@bot.on(NewMessage(pattern=r'/stats'))
async def broadcast_handler(event: MessageEvent):
    """
    /stats command handler.
    """
    lang_keys = await bot.loop.run_in_executor(
        None, partial(redis.keys, 'lang-*')
    )

    es_count = 0
    en_count = 0
    for lk in lang_keys:
        lang = await bot.loop.run_in_executor(
            None, partial(redis.get, lk)
        )
        if lang == b'es':
            es_count += 1
        elif lang == b'en':
            en_count += 1

    await event.respond(
        message=(
            '📊 Stats of the bot:\n'
            f'👥 Total of users: `{len(lang_keys)}`\n'
            f'🇪🇸 Spanish language: `{es_count}`\n'
            f'🇬🇧 English language: `{en_count}`'
        )
    )

    raise StopPropagation


async def main():
    await bot.run_until_disconnected()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
