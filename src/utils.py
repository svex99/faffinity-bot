from typing import List, Union
from bot_types import FAMovie


def humanize(data: FAMovie):
    """
    Humanize the movie data, modifies the data inplace.
    """
    for key in data:
        if data[key]:
            if isinstance(data[key], list):
                if isinstance(data[key][0], (str, int,)):
                    # avoid repeated values in list
                    clean_list = []
                    for entry in data[key]:
                        if entry not in clean_list:
                            clean_list.append(entry)

                    data[key] = ', '.join(entry for entry in clean_list)
        else:
            data[key] = '`-`'

    return data
