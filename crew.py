from api import api_call
from config import SETTINGS
from helpers import create_embed, LetterboxdError


async def crew_embed(input_name, cmd_alias):
    lbxd_id = __check_if_fixed_search(input_name)
    person_json = await __search_letterboxd(input_name, cmd_alias, lbxd_id)
    description, name, url, tmdb_id = __get_details(person_json)
    api_url = 'https://api.themoviedb.org/3/person/{}'.format(tmdb_id)
    description += await __get_dates(api_url)
    picture = await __get_picture(api_url)
    return create_embed(name, url, description, picture)


def __check_if_fixed_search(keywords):
    for name, lbxd_id in SETTINGS['fixed_crew_search'].items():
        if name.lower() == keywords.lower():
            return lbxd_id
    return ''


async def __search_letterboxd(item, cmd_alias, lbxd_id):
    if lbxd_id:
        person_json = await api_call('contributor/' + lbxd_id)
    else:
        params = {'input': item, 'include': 'ContributorSearchItem'}
        if cmd_alias in ['actress', 'actor']:
            params['contributionType'] = 'Actor'
        elif cmd_alias == 'director':
            params['contributionType'] = 'Director'
        response = await api_call('search', params)
        if not response['items']:
            raise LetterboxdError('No person was found with this search.')
        person_json = response['items'][0]['contributor']
    return person_json


def __get_details(person_json):
    for link in person_json['links']:
        if link['type'] == 'tmdb':
            tmdb_id = link['id']
        elif link['type'] == 'letterboxd':
            url = link['url']
    description = ''
    for contrib_stats in person_json['statistics']['contributions']:
        description += '**' + contrib_stats['type'] + ':** '
        description += str(contrib_stats['filmCount']) + '\n'
    return description, person_json['name'], url, tmdb_id


async def __get_dates(api_url):
    details_text = ''
    url = api_url + '?api_key={}'.format(SETTINGS['tmdb'])
    person_tmdb = await api_call(url, None, False)
    for element in person_tmdb:
        if not person_tmdb[element]:
            continue
        if element == 'birthday':
            details_text += '**Birthday:** ' + person_tmdb[element] + '\n'
        elif element == 'deathday':
            details_text += '**Day of Death:** ' + person_tmdb[element] + '\n'
        elif element == 'place_of_birth':
            details_text += '**Place of Birth:** ' + person_tmdb[element]
    return details_text


async def __get_picture(api_url):
    api_url += '/images?api_key=' + SETTINGS['tmdb']
    person_img = await api_call(api_url, None, False)
    if not person_img or not person_img['profiles']:
        return ''
    highest_vote = 0
    for img in person_img['profiles']:
        if img['vote_average'] >= highest_vote:
            highest_vote = img['vote_average']
            path = img['file_path']
    return 'https://image.tmdb.org/t/p/w200' + path
