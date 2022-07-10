# faffinity-bot

[🇪🇸 Leer versión en español](/README_es.md)

Telegram bot to get info from https://filmaffinity.com.

You can find it at Telegram: [@faffinitybot](https://t.me/faffinitybot).

## 🤖 How to run the bot

1. Rename the `data/.env.example` file to `data/.env` and configure inside the environment variables properly:

- `API_ID` - your api ID from https://my.telegram.org.
- `API_HASH` - your api hash from https://my.telegram.org.
- `BOT_TOKEN` - token of the bot your created with [@botfather](https://t.me/botfather).
- `ADMIN_ID` - your Telegram account ID.

2. Make sure you have installed `docker` and `make`, go to the root folder of the project and run the next commands:

```
❯ make init-db
❯ make build-prod
❯ make run-prod
```

3. To stop the bot:

```
❯ make down
```

## 📌 TODO

- Get Screenwriter, Music and Cinematography for `en` language.
- Download trailer.
- Show more stats to admin.

## 👏 Credits

Special thanks to these projects.
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [python_filmaffinity](https://github.com/sergiormb/python_filmaffinity)

<hr>

>### Disclaimer
>This bot is not associated to FilmAffinity. It is a personal project and is hosted by myself, so it can go offline without previous advice.
