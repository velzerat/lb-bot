from random import randrange
from film import film_embed
from api import api_call

async def random_embed():
    film_list = await api_call('list/Lb60/entries')
    random_int = randrange(len(film_list)['items'])
    film = film_list['items'][random_int]

    return await film_embed(film['film']['name'])
