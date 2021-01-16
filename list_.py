from api import api_call
from helpers import create_embed, format_text, LetterboxdError
from user import user_details


async def list_embed(username, keywords):
    __, __, user_lbxd_id, __ = await user_details(username)
    list_id = await __find_list(keywords, user_lbxd_id)
    description, url, poster_url, name = await __get_infos(list_id)
    return create_embed(name, url, description, poster_url)


async def __find_list(keywords, user_lbxd_id):
    params = {
        'member': user_lbxd_id,
        'memberRelationship': 'Owner',
        'perPage': 50,
        'where': 'Published'
    }
    response = await api_call('lists', params)
    match = False
    for user_list in response['items']:
        for word in keywords.lower().split():
            if word in user_list['name'].lower():
                match = True
            else:
                match = False
                break
        if match:
            return user_list['id']
    raise LetterboxdError('No list was found (limit to 50 most recent).\n' +
                          'Make sure the first word is a **username**.')


async def __get_infos(list_id):
    list_json = await api_call('list/{}'.format(list_id))
    for link in list_json['links']:
        if link['type'] == 'letterboxd':
            url = link['url']
            break
    description = 'By **' + list_json['owner']['displayName'] + '**\n'
    description += str(list_json['filmCount']) + ' films\nPublished '
    description += list_json['whenPublished'].split('T')[0].strip() + '\n'
    if list_json.get('descriptionLbml'):
        description += format_text(list_json['descriptionLbml'], 300)
    if list_json['previewEntries']:
        poster_json = list_json['previewEntries'][0]['film'].get('poster')
        if not poster_json:
            return description, url, None, list_json['name']
        for poster in poster_json['sizes']:
            if poster['height'] > 400:
                poster_url = poster['url']
                break
    return description, url, poster_url, list_json['name']
