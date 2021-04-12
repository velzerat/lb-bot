from random import randrange
from film import film_embed
from api import api_call

async def random_embed():

    with open("films.txt") as f:
        film = random_line(f)

    return await film_embed(film)

def random_line(afile, default=None):
    line = default
    for i, aline in enumerate(afile, start=1):
        if randrange(i) == 0:  # random int [0..i)
            line = aline
    return line


print(line)
