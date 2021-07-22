# faffinity-bot

[🇬🇧 Read English version](/README.md)

Bot de Telegram para obtener información de https://filmaffinity.com.

Puedes encontrarlo en Telegram: [@faffinitybot](https://t.me/faffinitybot).

## 🤖 Como ejecutar el bot

1. Renombra el archivo `.env.example` a `.env` y configura dentro las variables de entorno adecuadamente:

- `API_ID` - tu api ID de https://my.telegram.org.
- `API_HASH` - tu api hash de https://my.telegram.org.
- `BOT_TOKEN` - token del bot que creaste con [@botfather](https://t.me/botfather).
- `ADMIN_ID` - ID de tu cuenta en Telegram.
- `REDIS_HOST` - host del servicio de redis que va a funcionar como caché (si vas a usar `docker-compose` puedes asinarle `redis` a esta variable).

2. Make sure you have installed docker and docker-compose, go to the root folder of the project and run the command:

2. Verifica que tengas instalado docker y docker-compose, ve a la raíz del proyecto y ejecuta el comando:


```
docker-compose up -d --build
```

## 📌 TODO

- [ ] Obtener Screenwriter, Music y Cinematography para el lenguaje `en`.
- [ ] Añadir soporte inline.
- [ ] Descargar álbum completo de fotos.
- [ ] Descargar tráiler.
- [ ] Emitir mensaje a los usuarios del bot.

## 👏 Créditos

Agradecimientos especiales a estos poyectos.
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [python_filmaffinity](https://github.com/sergiormb/python_filmaffinity)

<hr>

>### Negante
>Este bot no está asocidado a FilmAffinity. Es un poyecto personal y es hopedado bajo mis posibilidades, por tanto puede pasar a estar offline sin aviso previo.
