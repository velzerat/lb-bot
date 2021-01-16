from re import fullmatch

from api import api_call
from config import SETTINGS
from helpers import create_embed, LetterboxdError


async def film_embed(keywords, with_mkdb=False):
    input_year = __check_year(keywords)
    lbxd_id = __check_if_fixed_search(keywords)
    film_json = await __search_request(keywords, input_year, lbxd_id)
    lbxd_id = film_json['id']
    title = film_json['name']
    year = film_json.get('releaseYear')
    lbxd_url, tmdb_id, poster_path = __get_links(film_json)
    description = await __create_description(lbxd_id, tmdb_id, title)
    if with_mkdb:
        description += await __get_mkdb_rating(lbxd_url)
    description += await __get_stats(lbxd_id)
    if year:
        title += ' (' + str(year) + ')'
    return create_embed(title, lbxd_url, description, poster_path)


async def film_details(keywords):
    input_year = __check_year(keywords)
    lbxd_id = __check_if_fixed_search(keywords)
    film_json = await __search_request(keywords, input_year, lbxd_id)
    lbxd_id = film_json['id']
    title = film_json['name']
    year = film_json.get('releaseYear')
    lbxd_url, _, poster_path = __get_links(film_json)
    return lbxd_id, title, year, poster_path, lbxd_url


def __check_year(keywords):
    last_word = keywords.split()[-1]
    if fullmatch(r'\(\d{4}\)', last_word):
        return last_word.replace('(', '').replace(')', '')
    return ''


def __check_if_fixed_search(keywords):
    for title, lbxd_id in SETTINGS['fixed_film_search'].items():
        if title.lower() == keywords.lower():
            return lbxd_id
    return ''


async def __search_request(keywords, input_year, lbxd_id):
    found = False
    if input_year:
        keywords = ' '.join(keywords.split()[:-1])
    if lbxd_id:
        film_json = await api_call('film/{}'.format(lbxd_id))
        return film_json
    params = {'input': keywords, 'include': 'FilmSearchItem'}
    response = await api_call('search', params)
    if not response.get('items'):
        raise LetterboxdError('No film was found with this search.')
    results = response['items']
    if input_year:
        for result in results:
            if not result['film'].get('releaseYear'):
                continue
            film_year = str(result['film']['releaseYear'])
            if film_year == input_year:
                film_json = result['film']
                found = True
                break
    else:
        film_json = results[0]['film']
    if input_year and not found:
        raise LetterboxdError('No film was found with this search.')
    return film_json


def __get_links(film_json):
    for link in film_json['links']:
        if link['type'] == 'letterboxd':
            lbxd_url = link['url']
        elif link['type'] == 'tmdb':
            tmdb_id = link['id']

    poster_path = ''
    if film_json.get('poster'):
        for poster in film_json['poster']['sizes']:
            if poster['height'] > 400:
                poster_path = poster['url']
                break
        if not poster_path:
            poster_path = film_json['poster']['sizes'][0]['url']
    return lbxd_url, tmdb_id, poster_path


async def __create_description(lbxd_id, tmdb_id, title):
    description = ''
    film_json = await api_call('film/{}'.format(lbxd_id))

    original_title = film_json.get('originalName')
    if original_title:
        description += '**Original Title:** ' + original_title + '\n'

    director_str = ''
    for contribution in film_json['contributions']:
        if contribution['type'] == 'Director':
            for dir_count, director in enumerate(contribution['contributors']):
                director_str += director['name'] + ', '
            break
    if director_str:
        if dir_count:
            description += '**Directors:** '
        else:
            description += '**Director:** '
        description += director_str[:-2] + '\n'

    description += await __get_countries(tmdb_id, title)
    runtime = film_json.get('runTime')
    description += '**Length:** ' + str(runtime) + ' mins\n' if runtime else ''

    genres_str = ''
    for genres_count, genre in enumerate(film_json['genres']):
        genres_str += genre['name'] + ', '
    if genres_str:
        if genres_count:
            description += '**Genres:** '
        else:
            description += '**Genre:** '
        description += genres_str[:-2] + '\n'

    return description


async def __get_countries(tmdb_id, title):
    api_url = 'https://api.themoviedb.org/3/movie/' + tmdb_id\
                + '?api_key=' + SETTINGS['tmdb']
    country_text = ''
    country_str = ''
    response = await api_call(api_url, None, False)
    if response and response['title'] == title:
        for count, country in enumerate(response['production_countries']):
            if country['name'] == 'United Kingdom':
                country_str += 'UK, '
            elif country['name'] == 'United States of America':
                country_str += 'USA, '
            else:
                country_str += country['name'] + ', '
        if country_str:
            if count:
                country_text += '**Countries:** '
            else:
                country_text += '**Country:** '
            country_text += country_str[:-2] + '\n'
    return country_text


async def __get_mkdb_rating(lbxd_url):
    mkdb_url = lbxd_url.replace('letterboxd.com', 'eiga.me/api')
    response = await api_call(mkdb_url + 'summary', None, False)
    if not response or not response['total']:
        return ''
    mkdb_description = '**MKDb Average:** [' + str(response['mean'])
    mkdb_description += ' / ' + str(response['total']) + ' ratings\n]'
    mkdb_description += '(' + mkdb_url.replace('/api', '') + ')'
    return mkdb_description


async def __get_stats(lbxd_id):
    text = ''
    stats_json = await api_call('film/{}/statistics'.format(lbxd_id))
    views = stats_json['counts']['watches']
    if views > 9999:
        views = str(round(views / 1000)) + 'k'
    elif views > 999:
        views = str(round(views / 1000, 1)) + 'k'
    if stats_json.get('rating'):
        ratings_count = stats_json['counts']['ratings']
        if ratings_count > 999:
            ratings_count = str(round(ratings_count / 1000, 1)) + 'k'
        text += '**Average Rating:** ' + str(round(stats_json['rating'], 2))
        text += ' / ' + str(ratings_count) + ' ratings\n'
    text += 'Watched by ' + str(views) + ' members'
    return text
