from bot_types import FAMovie


def humanize(data: FAMovie) -> None:
    """
    Humanize the movie data, modifies the data inplace.
    """
    for key in data:
        if data[key]:
            if isinstance(data[key], list):
                if isinstance(data[key][0], (str, int,)):
                    data[key] = ', '.join(entry for entry in set(data[key]))
        else:
            data[key] = '`-`'
