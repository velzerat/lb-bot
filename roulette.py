from random import randrange
from film import film_embed
from api import api_call
import os

async def random_embed():
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    f = open(os.path.join(__location__, "films.txt"), "r", encoding="utf8", errors="ignore")

    film = random_line(f)
    f.close()
    return await film_embed(film)

def random_line(afile, default=None):
    line = default
    for i, aline in enumerate(afile, start=1):
        if randrange(i) == 0:  # random int [0..i)
            line = aline
    return line
