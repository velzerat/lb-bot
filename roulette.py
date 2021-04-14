from random import randrange
from film import film_embed
from api import api_call
import os
from user import user_details

async def random(username):

    if not username: #get movie from file, when no username is given
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        f = open(os.path.join(__location__, "films.txt"), "r")
        film = random_line(f)
        f.close()
        return await film_embed(film)

    else: #pick from user watchlist
        __, __, user_lbxd_id, __ = await user_details(username)
        film = await __get_watchlist(user_lbxd_id)
        return await film_embed(film)

async def __get_watchlist(user_lbxd_id):
    params = {
        'sort': 'Shuffle',
        'perPage': 20,
        'where': 'Released'
    }

    watchlist_json = await api_call('contributor/' + lbxd_id + '/watchlist', params)
    film_title = watchlist_json['items'][0]['name']
    return film_title


def random_line(afile, default=None):
    line = default
    for i, aline in enumerate(afile, start=1):
        if randrange(i) == 0:  # random int [0..i)
            line = aline
    return line
