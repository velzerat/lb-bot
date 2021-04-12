from random import randrange
from film import film_embed
from api import api_call

async def random_embed():
    film_list = await api_call('list/Lb60/entries')
    film = film_list['items'][randrange(len(film_list))]

    return await film_embed(film['film']['name'])
