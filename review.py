from api import api_call
from film import film_details
from helpers import create_embed, format_text, LetterboxdError
from user import user_details


async def review_embed(username, film_search):
    username, display_name, user_id, __ = await user_details(username)
    film_id, film_title, film_year, poster_path, film_url = await film_details(
        film_search)
    activity_url = film_url.replace(
        '.com/', '.com/{}/'.format(username)) + 'activity'
    response, nb_entries = await __find_entries(user_id, display_name,
                                                film_id, film_title, film_year)
    description, embed_url = __create_description(response, activity_url)

    if nb_entries > 1:
        embed_url = activity_url
    entry_word = 'entries' if nb_entries > 1 else 'entry'
    title = '{0} {1} of {2} ({3})'.format(display_name, entry_word,
                                          film_title, film_year)
    return create_embed(title, embed_url, description, poster_path)


async def __find_entries(user_id, display_name, film_id, film_title, film_year):
    params = {
        'film': film_id,
        'member': user_id,
        'memberRelationship': 'Owner'
    }
    response = await api_call('log-entries', params)
    nb_entries = len(response['items'])
    if not nb_entries:
        raise LetterboxdError(
            '{0} does not have logged activity for {1} ({2}).'.format(
                display_name, film_title, film_year))
    return response, nb_entries


def __create_description(response, activity_url):
    description = ''
    preview_done = False
    for entry in response['items']:
        if len(description) > 1500:
            description += '**[Click here for more activity]({})**'.format(
                activity_url)
            break
        for link in entry['links']:
            if link['type'] == 'letterboxd':
                entry_link = link['url']
                break
        word = 'Entry'
        if entry.get('review'):
            word = 'Review'
        description += '**[{}]('.format(word) + entry_link + ')** '
        if entry.get('diaryDetails'):
            date = entry['diaryDetails']['diaryDate']
            description += '**' + date + '** '
        if entry.get('rating'):
            description += '★' * int(entry['rating'])
            if str(entry['rating'])[-1] == '5':
                description += '½'
        if entry['like']:
            description += ' ♥'
        description += '\n'
        if not preview_done:
            preview = __create_preview(entry)
            if preview:
                description += preview
                preview_done = True
    return description, entry_link


def __create_preview(review):
    preview = ''
    if review.get('review'):
        if review['review']['containsSpoilers']:
            preview += '```This review may contain spoilers.```'
        else:
            preview += format_text(review['review']['lbml'], 400)
    return preview
