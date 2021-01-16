from api import api_call
from helpers import create_embed
from user import user_details


async def diary_embed(username):
    username, display_name, user_id, avatar_url = await user_details(username)
    url = 'https://letterboxd.com/{}/films/diary'.format(username)
    title = 'Recent diary activity from {}'.format(display_name)
    description = await __get_activity(user_id)
    return create_embed(title, url, description, avatar_url)


async def __get_activity(lbxd_id):
    params = {
        'member': lbxd_id,
        'memberRelationship': 'Owner',
        'where': 'HasDiaryDate'
    }
    response = await api_call('log-entries', params)
    description = ''
    for n_entries, diary_entry in enumerate(response['items']):
        if n_entries > 4:
            break
        for link in diary_entry['links']:
            if link['type'] == 'letterboxd':
                entry_url = link['url']
                break
        description += '**[' + diary_entry['film']['name']
        film_year = diary_entry['film'].get('releaseYear')
        if film_year:
            description += ' ({})'.format(film_year)
        description += ']({})**\n'.format(entry_url)
        if diary_entry.get('diaryDetails'):
            description += '**' + \
                diary_entry['diaryDetails']['diaryDate'] + '** '
        if diary_entry.get('rating'):
            description += '★' * int(diary_entry['rating'])
            if str(diary_entry['rating'])[-1] == '5':
                description += '½'
        if diary_entry['like']:
            description += ' ♥'
        if diary_entry['diaryDetails']['rewatch']:
            description += ' ↺'
        if diary_entry.get('review'):
            description += ' ☰'
        description += '\n'
    return description
