from __future__ import annotations
import os
import logging
import asyncio
import urllib3
import json
from functools import partial
from datetime import datetime
from pathlib import Path

import dotenv
import aiosqlite
from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery, StopPropagation, \
    InlineQuery
from telethon.tl.types import InputWebDocument
from telethon.errors.rpcerrorlist import MediaCaptionTooLongError, \
    WebpageMediaEmptyError, UserIsBlockedError, UserIsBotError, \
    PeerIdInvalidError, ChannelPrivateError, ChatWriteForbiddenError, \
    ChatAdminRequiredError, InputUserDeactivatedError
from python_filmaffinity import FilmAffinity
from python_filmaffinity.exceptions import FilmAffinityConnectionError

import keyboards as kbs
from bot_types import MessageEvent, CallbackMessageEventLike
from utils import humanize, TelegramLogsHandler, get_random_ad


dotenv.load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
SESSION = Path("data/faffinity-bot.session")
DB = Path("data/bot-db.sqlite")
NO_IMAGE = "https://www.filmaffinity.com/imgs/movies/noimgfull.jpg"
TRANSLATIONS = json.load(open("files/i18n_messages.json"))
ADS_FILE = Path("data/ads.json")
with ADS_FILE.open(encoding="utf8") as ads_file:
    ADS = json.load(ads_file)
START_TIME = datetime.now()
MOVIES_SEEN = 0

bot = TelegramClient(str(SESSION), API_ID, API_HASH)

logging.basicConfig(
    format="[%(levelname)s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        TelegramLogsHandler(bot, ADMIN_ID)
    ]
)

urllib3.disable_warnings()

# Spanish FA client
fa_es = FilmAffinity(lang="es", cache_path="data")
# English FA client
fa_en = FilmAffinity(lang="en", cache_path="data")
db_conn: aiosqlite.Connection | None = None


@bot.on(NewMessage(pattern=r"/start lang_(?P<lang>(es)|(en))"))
@bot.on(NewMessage())
@bot.on(CallbackQuery())
@bot.on(InlineQuery())
async def i18n_handler(event: CallbackMessageEventLike):
    """
    Sets the default language for this event.
    """
    if isinstance(event, NewMessage.Event) and event.pattern_match is not None:
        print(event.pattern_match, type(event))
        event_lang = event.pattern_match.groupdict().get("lang")
    else:
        event_lang = None

    async with db_conn.execute(
        "SELECT lang FROM user WHERE tid = ?",
        (event.sender_id, )
    ) as cursor:
        (lang, ) = (await cursor.fetchone()) or (None, )

    if lang is None:
        lang = event_lang or "es"
        await db_conn.execute(
            "INSERT INTO user (tid, lang) VALUES (?, ?)",
            (event.sender_id, lang, )
        )
        await db_conn.commit()

    event.lang = lang
    event.i18n = lambda key: TRANSLATIONS[key][lang]
    if lang == "es":
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
                title=_("fa_error"),
                text=_("fa_error")
            )
        ])
        logging.error(e)
    else:
        if result:
            await event.answer([
                builder.article(
                    title=movie["title"],
                    text=_("inline_result").format(**humanize(movie)),
                    thumb=InputWebDocument(
                        url=movie["poster"],
                        size=1,
                        mime_type="image/jpg",
                        attributes=[]
                    ) if movie["poster"] != "/imgs/movies/noimgfull.jpg" else None,
                    link_preview=False,
                    buttons=kbs.inline_details(_, fa.lang, movie["id"])
                )
                for movie in result
            ])
        else:
            await event.answer([
                builder.article(
                    title=_("no_matches").format(query=event.text),
                    text=_("no_matches").format(query=event.text),
                )
            ])


@bot.on(NewMessage())
@bot.on(CallbackQuery())
async def private_door(event: MessageEvent | CallbackQuery.Event):
    """
    Avoids handling of events in groups and channels for next handlers.
    """
    if not event.is_private:
        raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"delete(_(?P<msg_1>\d+))?"))
async def delete_handler(event: CallbackQuery.Event):
    """
    Deletes the message of the button clicked and max 2 messages more.
    """
    msg_1 = event.pattern_match["msg_1"]

    messages_to_delete = [event.message_id]
    if msg_1 is not None:
        messages_to_delete.append(int(msg_1))

    await bot.delete_messages(
        entity=event.sender_id,
        message_ids=messages_to_delete
    )

    raise StopPropagation


@bot.on(NewMessage(pattern=r"/start( lang_((es)|(en))_id_(?P<id>\d+))?"))
async def start_handler(event: MessageEvent):
    """
    /start command handler.
    """
    _ = event.i18n
    mid = event.pattern_match["id"]

    if not mid:
        await event.respond(_("start"))

        raise StopPropagation


@bot.on(NewMessage(pattern="/help"))
async def help_handler(event: MessageEvent):
    """
    /help command handler.
    """
    _ = event.i18n

    admin_help = (
        "\n\n##### Admin help #####\n"
        "/session - get the session file.\n"
        "/broadcast `<lang>|all` - broadcast a message to users of the bot.\n"
        "/stats - stats of the bot.\n"
        "/ads - list of active ads.\n"
    ) if event.sender_id == ADMIN_ID else ""

    await event.respond(
        message=_("help") + admin_help,
        buttons=kbs.hide(_)
    )

    raise StopPropagation


@bot.on(NewMessage(pattern="/support"))
async def support_handler(event: MessageEvent):
    """
    /support command handler.
    """
    _ = event.i18n

    await event.respond(
        message=_("support"),
        buttons=kbs.support(_),
        link_preview=False
    )

    raise StopPropagation


@bot.on(NewMessage(pattern=r"(?P<title>[^/].*)"))
@bot.on(NewMessage(pattern=r"/cast (?P<cast>.+)"))
@bot.on(NewMessage(pattern=r"/director (?P<director>.+)"))
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
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        if result:
            await event.respond(
                message=_("query_results"),
                buttons=kbs.search_result(_, result)
            )
        else:
            await event.respond(
                message=_("no_matches").format(
                    query=(
                        query.get("title") or
                        query.get("cast") or
                        query.get("director") or
                        "`-`"
                    )
                )
            )

    raise StopPropagation


@bot.on(NewMessage(pattern=r"/start lang_((es)|(en))_id_(?P<id>\d+)"))
@bot.on(CallbackQuery(pattern=rb"film_(?P<id>\d+)"))
async def movie_handler(event: CallbackMessageEventLike):
    """
    Shows the details about an specific movie.

    The movie id can be received from a click in an inline button or a link
    to the bot with the parameter start properly set.
    """
    global MOVIES_SEEN
    MOVIES_SEEN += 1

    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match["id"]
    if isinstance(mid, bytes):
        mid = mid.decode("utf8")

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{"id": mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        poster = movie["poster"] or NO_IMAGE
        humanize(movie)
        message = _("movie_template").format(**movie) + get_random_ad(_, ADS)

        try:
            await event.respond(
                message=message,
                file=poster,
                buttons=kbs.movie_keyboard(_, movie["id"]),
                link_preview=False
            )
        except MediaCaptionTooLongError:
            poster_msg = await event.respond(
                file=poster
            )
            await event.respond(
                message=message,
                buttons=kbs.movie_keyboard(
                    _,
                    mid=movie["id"],
                    linked_msg_ids=[poster_msg.id]
                ),
                link_preview=False
            )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"synopsis_(?P<id>\d+)"))
async def synopsis_handler(event: CallbackQuery.Event):
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match["id"].decode("utf8")

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{"id": mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        await event.respond(
            message=(
                f"ℹ **{_('Synopsis')}: "
                "{title}** ℹ\n\n{description}".format(**movie) +
                get_random_ad(_, ADS)
            ),
            buttons=kbs.hide(_),
            link_preview=False
        )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"awards_(?P<id>\d+)"))
async def awards_handler(event: CallbackQuery.Event):
    lang = event.lang
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match["id"].decode("utf8")

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{"id": mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        awards = movie["awards"]
        if awards:
            awards_text = f"🏆 **{_('Awards')}: {movie['title']}** 🏆\n\n"
            final = ""

            for a in awards:
                if a["year"].isalnum():
                    awards_text += f"🔸 `{a['year']}`: {a['award']}\n"
                else:
                    final = f"↗ {a['year']}"

            awards_text += (
                f"\n[{final if final else _('see_at_fa')}]"
                f"(https://www.filmaffinity.com/{lang}/film{movie['id']}.html)"
            )

            await event.respond(
                message=awards_text + get_random_ad(_, ADS),
                buttons=kbs.hide(_),
                link_preview=False
            )
        else:
            await event.respond(_("no_awards"))

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"reviews_(?P<id>\d+)"))
async def reviews_handler(event: CallbackQuery.Event):
    lang = event.lang
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match["id"].decode("utf8")

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{"id": mid})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        reviews = movie["reviews"]
        if reviews:
            reviews_text = (
                f"💭 **{_('Reviews')}: {movie['title']}** 💭\n"
            )

            for r in reviews:
                # remove `[` and `]` for don't break telegram markdown
                actual_review = r["review"].replace("[", "")
                actual_review = actual_review.replace("]", "")
                reviews_text += (
                    f"\n👤 [{r['author']}]"
                    f"({r['url'] or f'www.filmaffinity.com/{lang}/film{mid}.html'})\n"
                    f"💭 __{actual_review}__\n"
                )

            reviews_text += (
                f"\n[{_('see_at_fa')}]"
                f"(www.filmaffinity.com/{lang}/pro-reviews.php?movie-id={mid})"
            )

            await event.respond(
                message=reviews_text + get_random_ad(_, ADS),
                buttons=kbs.hide(_),
                link_preview=False
            )
        else:
            await event.respond(_("no_reviews"))

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"images_(?P<id>\d+)"))
async def images_handler(event: CallbackQuery.Event):
    """
    Sends images of a movie. Sends as max 10 images.
    """
    _ = event.i18n
    fa = event.fa_client
    mid = event.pattern_match["id"].decode("utf8")

    try:
        movie = await bot.loop.run_in_executor(
            None, partial(fa.get_movie, **{"id": mid, "images": True})
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        images = [
            still["image"] for still in movie["images"]["stills"]
            if still["image"]
        ]
        if images:
            try:
                await event.respond(file=images[:10])
            except WebpageMediaEmptyError as e:
                await event.respond(_("no_images"))
                logging.error(e)
        else:
            await event.respond(_("no_images"))

    raise StopPropagation


@bot.on(NewMessage(pattern="/language"))
async def language_handler(event: MessageEvent):
    """
    Sends a keyboard for language configuration.
    """
    await event.respond(
        message=TRANSLATIONS["select_lang"]["es"],
        buttons=kbs.select_lang()
    )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=b"lang_(?P<lang>es|en)"))
async def select_language_handler(event: MessageEvent):
    """
    Handles the language selection by the user.
    """
    lang = event.pattern_match["lang"].decode("utf8")

    await db_conn.execute(
        "UPDATE user SET lang = ? WHERE tid = ?",
        (lang, event.sender_id, )
    )
    await db_conn.commit()

    await event.edit(
        text=TRANSLATIONS["lang_selected"][lang]
    )

    raise StopPropagation


@bot.on(NewMessage(pattern="/top"))
async def top_handler(event: MessageEvent):
    """
    /top command handler.
    """
    _ = event.i18n

    await event.respond(
        message=_("select_top"),
        buttons=kbs.tops(_)
    )

    raise StopPropagation


@bot.on(CallbackQuery(pattern=rb"top_(?P<service>\w+)"))
async def select_language_handler(event: MessageEvent):
    """
    Handles the top selection by the user.
    """
    _ = event.i18n
    fa: FilmAffinity = event.fa_client
    service = event.pattern_match["service"].decode("utf8")

    top_services = {
        "HBO": fa.top_hbo,
        "Netflix": fa.top_netflix,
        "Filmin": fa.top_filmin,
        "Movistar": fa.top_movistar,
        "Rakuten": fa.top_rakuten,
    }

    try:
        result = await bot.loop.run_in_executor(
            None, partial(top_services[service], 40)
        )
    except FilmAffinityConnectionError as e:
        await event.respond(_("fa_error"))
        logging.error(e)
    else:
        text = f"🔝 Top {service} 🔝\n\n" + "\n\n".join(
            [
                "`%2d.` " % i + (
                    "[{title}](https://t.me/faffinitybot?start=id_{id})\n"
                    "📅 {year}      ⭐ {rating}/10"
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


@bot.on(NewMessage(pattern="/ads"))
async def list_ads_handler(event: MessageEvent):
    """
    Lists the ads saved in files/ads.json.
    """
    text = "\n`---------------`\n".join(
        f"/change_ad_{i}\n{ADS[i]}" for i in range(len(ADS))
    )

    await event.respond(text)

    raise StopPropagation


@bot.on(NewMessage(pattern=r"/change_ad_(?P<index>[0-4]) (?P<new_ad>.+)"))
async def change_ad_handler(event: MessageEvent):
    """
    Changes and saves in files/ads.json an specific ad.
    """
    global ADS

    index = int(event.pattern_match["index"])
    new_ad = event.pattern_match["new_ad"]
    if new_ad == "-":
        new_ad = ""

    ADS[index] = new_ad
    with ADS_FILE.open("w", encoding="utf8") as ads_file:
        json.dump(ADS, ads_file, indent=4)

    await event.respond(f"Ad saved:\n{new_ad}")

    raise StopPropagation


@bot.on(NewMessage(pattern="/session"))
async def session_handler(event: MessageEvent):
    """
    /session command handler.
    Returns the bot session file.
    """
    format_ = "%Y-%m-%d %H:%M:%S %Z%z"
    await event.respond(
        message=f"`{datetime.now().strftime(format_)}`",
        file=SESSION
    )

    raise StopPropagation


@bot.on(NewMessage(pattern=r"/broadcast (?P<lang>(es)|(en)|(all))"))
async def broadcast_handler(event: MessageEvent):
    """
    /broadcast command handler.
    """
    msg = await event.get_reply_message()

    if msg:
        lang = event.pattern_match["lang"]
        if lang == "all":
            users_query = db_conn.execute("SELECT tid FROM user")
            total_query = db_conn.execute("SELECT COUNT() FROM user")
        else:
            users_query = db_conn.execute(
                "SELECT tid FROM user WHERE lang = ?",
                (lang, )
            )
            total_query = db_conn.execute(
                "SELECT COUNT() FROM user WHERE lang = ?",
                (lang, )
            )

        async with total_query as cursor:
            (total, ) = await cursor.fetchone()

        text = (
            '📢 Broadcasting to `{}` users...\n'
            '🚫 Errors: `{}`\n'
            '✅ Broadcast: `{}/{}`'
        )
        count = 0
        errors = 0
        progress_msg = await event.respond(
            message=text.format(lang, errors, count - errors, total)
        )
        step = (total + 50) // 50
        async with users_query as cursor:
            async for (tid, ) in cursor:
                count += 1

                try:
                    await bot.send_message(
                        entity=tid,
                        message=msg
                    )
                except (
                    ValueError,
                    UserIsBlockedError,
                    UserIsBotError,
                    PeerIdInvalidError,
                    ChannelPrivateError,
                    ChatWriteForbiddenError,
                    ChatAdminRequiredError,
                    InputUserDeactivatedError
                ):
                    errors += 1
                except Exception as e:
                    errors += 1
                    await event.respond(
                        message=(
                            f"Exception: `{type(e)}: {e}`\n\n"
                            f"At user `{count}`. Sleeping `30` seconds..."
                        )
                    )
                    await asyncio.sleep(30)

                await asyncio.sleep(0.25)

                if count % step == 0 or count == total:
                    await progress_msg.edit(
                        text=text.format(lang, errors, count - errors, total)
                    )

        await event.respond(
            message="✅ Done!!!",
            reply_to=progress_msg
        )
    else:
        await event.respond("⚠ You must reply to a message with /broadcast command.")

    raise StopPropagation


@bot.on(NewMessage(pattern=r"/stats"))
async def stats_handler(event: MessageEvent):
    """
    /stats command handler.
    """
    async with db_conn.execute("SELECT COUNT() FROM user") as cursor:
        (total_count, ) = await cursor.fetchone()

    async with db_conn.execute("SELECT COUNT() FROM user WHERE lang = 'es'") as cursor:
        (es_count, ) = await cursor.fetchone()

    async with db_conn.execute("SELECT COUNT() FROM user WHERE lang = 'en'") as cursor:
        (en_count, ) = await cursor.fetchone()

    uptime = str(datetime.now() - START_TIME).split(".")[0]

    if (cache := Path("data/cache-film-affinity.sqlite")).exists():
        cache_size = round(cache.stat().st_size / 1024 / 1024, 2)
    else:
        cache_size = 0

    await event.respond(
        message=(
            "📊 Stats of the bot:\n"
            f"👥 Total of users: `{total_count}`\n"
            f"🇪🇸 Spanish language: `{es_count}`\n"
            f"🇬🇧 English language: `{en_count}`\n"
            f"👀 Movies seen: `{MOVIES_SEEN}`\n"
            f"💾 Cache size: `{cache_size} MB`\n"
            f"⏱ Bot uptime: `{uptime}`\n"
        )
    )

    raise StopPropagation


async def main():
    global db_conn
    db_conn = await aiosqlite.connect(str(DB))
    await bot.start(bot_token=BOT_TOKEN)
    await bot.get_me()


async def stop():
    await bot.disconnect()
    await db_conn.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Stopping the bot...")
    finally:
        loop.run_until_complete(stop())
        print("Bot stopped")
