"""
Bot messages.
"""
start_command = (
    '👋 Hola, puedo buscar la información en FilmAffinity de películas, '
    'series, miniseries, cortos, documentales, etc.'
)

support_command = (
    'Quiero agradecerte de antemano por mostrar interés en leer este apartado.\n\n'
    '⭐️ Si te resulta útil este bot puedes apoyarlo dándole una estrella en GitHub, '
    '[el código es totalmente público](https://github.com/svex99/faffinity-bot). 😁\n\n'
    '🤲 También puedes dar tu apoyo realizando una donación para mantenerlo online 24/7, '
    'estaría muy agradecido, en tal caso, puedes contactarme @svex99.\n\n'
    '¡Gracias! '
)

help_command = (
    '💡 Puedes buscar las películas por título, actor o director.\n\n'
    '**1.** Para buscar por actor debes usar el comando /cast seguido del nombre del actor.\n'
    'Ejemplo: `/cast Leonardo DiCaprio`\n\n'
    '**2.** Para buscar por director debes usar el comando /director seguido del nombre del director.\n'
    'Ejemplo: `/director Quentin Tarantino`\n\n'
    '**3.** Para buscar por el nombre de la película simplemente envía un mensaje con él.'

)

movie_template = (
    '🎬 **Título:** [{title}](www.filmaffinity.com/es/film{id}.html)\n'
    '⭐️ **Calificación:** {rating}/10 ({votes} votos)\n'
    '📅 **Año:** {year}\n'
    '⏳ **Duración:** {duration}\n'
    '🗺 **País:** {country}\n'
    '👤 **Dirección:** {directors}\n'
    '✍️ **Guion:** {writers}\n'
    '🎵 **Música:** {music}\n'
    '📷 **Fotografía:** {cinematography}\n'
    '👥 **Reparto:** {actors}\n'
    '🔰 **Género:** {genre}\n'
    '🏢 **Productora:** {producers}\n'
)

movie_synopsis = (
    'ℹ **Sinopsis: {title}** ℹ\n\n'
    '{description}'

)

fa_error = (
    '❗️ Ha ocurrido un error solicitando la información a FilmAffinity. '
    'Inténtalo de nuevo.'
)
