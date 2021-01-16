import asyncio
import hashlib
import hmac
import string
import time
import uuid
from urllib.parse import urlencode

import aiohttp
from config import SETTINGS
from helpers import LetterboxdError

session = aiohttp.ClientSession(loop=asyncio.get_event_loop())


async def api_call(path, params=None, letterboxd=True, is_json=True):
    if not params:
        params = dict()
    api_url = path
    if params.get('input'):
        punc = string.punctuation
        params['input'] = "".join(l for l in params['input'] if l not in punc)
    if letterboxd:
        url = SETTINGS['letterboxd']['api_base'] + path
        params['apikey'] = SETTINGS['letterboxd']['api_key']
        params['nonce'] = str(uuid.uuid4())
        params['timestamp'] = int(time.time())
        url += '?' + urlencode(params)
        api_url = url + '&signature=' + __sign(url)
    async with session.get(api_url) as resp:
        if resp.status >= 500 and letterboxd:
            raise LetterboxdError('A request to the Letterboxd API failed.' +
                                  ' This may be due to a server issue.')
        elif resp.status >= 400:
            return ''
        if is_json:
            response = await resp.json()
        else:
            response = await resp.read()
    return response


async def post_call(path, params=None):
    if not params:
        params = dict()
    async with session.post(path, data=params) as resp:
        response = await resp.json()
    return response


def __sign(url, body=''):
    # Create the salted bytestring
    signing_bytestring = b'\x00'.join(
        [str.encode('GET'),
         str.encode(url),
         str.encode(body)])
    # applying an HMAC/SHA-256 transformation, using our API Secret
    signature = hmac.new(
        str.encode(SETTINGS['letterboxd']['api_secret']),
        signing_bytestring,
        digestmod=hashlib.sha256)
    # get the string representation of the hash
    signature_string = signature.hexdigest()
    return signature_string
