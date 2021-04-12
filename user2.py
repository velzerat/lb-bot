import os
import subprocess

from api import api_call, post_call
from config import SETTINGS
from helpers import create_embed, LetterboxdError


async def user_embed(username):
    username = username.lower()
    url = 'https://letterboxd.com/{}'.format(username)
    lbxd_id = __check_if_fixed_search(username)
    if not lbxd_id:
        lbxd_id = await __search_profile(username)
    member_json = await __get_userjson(lbxd_id)
    display_name, avatar_url, description = await __get_infos(member_json, lbxd_id)
    fav_text, fav_posters_link = __get_favs(member_json)
    description += fav_text
    return create_embed(display_name, url, description, avatar_url)


async def user_details(username):
    username = username.lower()
    lbxd_id = __check_if_fixed_search(username)
    if not lbxd_id:
        lbxd_id = await __search_profile(username)
    member_json = await __get_userjson(lbxd_id)
    display_name, avatar_url, __ = await __get_infos(member_json, lbxd_id, False)
    return username, display_name, lbxd_id, avatar_url


def __check_if_fixed_search(username):
    for fixed_username, lbxd_id in SETTINGS['fixed_user_search'].items():
        if fixed_username.lower() == username:
            return lbxd_id
    return ''


async def __search_profile(username):
    params = {
        'input': username.replace('_', ' '),
        'include': 'MemberSearchItem',
        'perPage': '100'
    }
    while True:
        response = await api_call('search', params)
        if not response['items']:
            break
        for result in response['items']:
            if result['member']['username'].lower() == username:
                return result['member']['id']
        if response.get('next'):
            params['cursor'] = response['next']
        else:
            break
    raise LetterboxdError('The user **' + username + '** wasn\'t found.')


async def __get_userjson(lbxd_id):
    member_response = await api_call('member/{}'.format(lbxd_id))
    if member_response == '':
        raise LetterboxdError(
            'The user wasn\'t found. ' +
            'They may have refused to be reachable via the API.')
    return member_response


async def __get_infos(member_json, lbxd_id, with_stats=True):
    display_name = member_json['displayName']
    avatar_url = member_json['avatar']['sizes'][-1]['url']
    description = '**'
    if with_stats:
        if member_json.get('location'):
            description += member_json['location']'
        stats_json = await api_call('member/{}/statistics'.format(lbxd_id))
        description += str(stats_json['counts']['watches']) + ' films watched ('
        description += str(stats_json['counts']['filmsInDiaryThisYear'])+' this year)**\n'
    return display_name, avatar_url, description


def __get_favs(member_json):
    description = ''
    fav_posters_link = list()
    for fav_film in member_json['favoriteFilms']:
        fav_name = fav_film['name']
        if fav_film.get('poster'):
            for poster in fav_film['poster']['sizes']:
                if 150 < poster['width'] < 250:
                    fav_posters_link.append(poster['url'])
        if fav_film.get('releaseYear'):
            fav_name += ' (' + str(fav_film['releaseYear']) + ')'
        for link in fav_film['links']:
            if link['type'] == 'letterboxd':
                fav_url = link['url']
        description += '[{0}]({1})\n'.format(fav_name, fav_url)
    return description, fav_posters_link


async def __upload_fav_posters(username, fav_posters_link):
    # Download posters
    if not os.path.exists(username):
        os.popen('mkdir ' + username)
    img_cmd = 'convert '
    for index, fav_poster in enumerate(fav_posters_link):
        img_data = await api_call(fav_poster, None, False, False)
        temp_fav = '{0}/fav{1}.jpg'.format(username, index)
        img_cmd += temp_fav + ' '
        with open(temp_fav, 'wb') as handler:
            handler.write(img_data)

    # Upload to Cloudinary
    img_cmd += '+append {}/fav.jpg'.format(username)
    subprocess.call(img_cmd, shell=True)
    with open('{}/fav.jpg'.format(username), 'rb') as pic:
        bin_pic = pic.read()
    os.popen('rm -r ' + username)
    upload_url = 'https://api.cloudinary.com/v1_1/'
    upload_url += SETTINGS['cloudinary']['cloud_name'] + '/image/upload'
    params = {'file': bin_pic,
              'upload_preset': SETTINGS['cloudinary']['preset']}
    result = await post_call(upload_url, params)
    return result['url']
