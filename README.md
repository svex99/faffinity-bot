# faffinity-bot

Telegram bot to get info from https://filmaffinity.com.

You can find it at Telegram: [@faffinitybot](https://t.me/faffinitybot).

## 🤖 How to run the bot

1. Rename your `.env.example` file to `.env` and configure inside the environment variables properly:

- `API_ID` - your api ID from https://my.telegram.org.
- `API_HASH` - your api hash from https://my.telegram.org.
- `BOT_TOKEN` - token of the bot your created with [@botfather](https://t.me/botfather).
- `ADMIN_ID` - your Telegram account ID.
- `REDIS_HOST` - redis service that is going to work as cache (if you are going to use `docker-compose` set this field to `redis`).

2. Make sure you have installed docker and docker-compose, go to the root folder of the project and run the command:

```
docker-compose up -d --build
```

## 📌 TODO

- [ ] Get Screenwriter, Music and Cinematography for `en` language.
- [ ] Add inline support.
- [ ] Download full album of photos.
- [ ] Download trailer.
- [ ] Broadcast message to users of the bot.

## 👏 Credits

Special thanks to these projects.
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [python_filmaffinity](https://github.com/sergiormb/python_filmaffinity)


>### Disclaimer
>This bot is not associated to FilmAffinity. It is a personal project and is hosted by myself, so it can go offline without previous advice.
