import asyncio
import calendar
import datetime
import json
import random
import requests
import os
import pprint
from time import sleep
from time import strftime
from winrt.windows.storage.streams import \
    DataReader, Buffer, InputStreamOptions
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager

def get_default_status_emoji():
        return random.choice([
        ':cd:',
        ':headphones:',
        ':musical_note:',
        ':notes:',
        ':radio:',
    ])

async def read_stream_into_buffer(stream_ref, buffer):
    readable_stream = await stream_ref.open_read_async()
    readable_stream.read_async(buffer, buffer.capacity, InputStreamOptions.READ_AHEAD)

def get_local_file():
    thumb_stream_ref = current_media_info['thumbnail']

    if thumb_stream_ref is None:
        return False

    thumb_read_buffer = Buffer(5000000)
    asyncio.run(read_stream_into_buffer(thumb_stream_ref, thumb_read_buffer))
    buffer_reader = DataReader.from_buffer(thumb_read_buffer)
    byte_buffer = buffer_reader.read_bytes(thumb_read_buffer.length)
    local_filename = 'media_thumb.jpg'

    with open(local_filename, 'wb+') as fobj:
        fobj.write(bytearray(byte_buffer))

    return local_filename


def delete_slack_emoji():
    postBody = {
        'token': slack_token,
        'name': emoji_name,
    }
    
    r = requests.post(
        'https://slack.com/api/emoji.remove',
        data = postBody
    )

    if(r.ok):
        parsed = json.loads(r.text)
        if parsed['ok']:
            return True
        else:
            return False
    else:
        r.raise_for_status()
    
    return False

def ensure_slack_does_not_have_emoji():
    r = requests.get(
        'https://slack.com/api/emoji.list',
        params = {'token': slack_token}
    )

    if(r.ok):
        parsed = json.loads(r.text)
        
        if parsed['ok']:
            if emoji_name in parsed['emoji']:
                return delete_slack_emoji()
            else:
                return True
        else:
            return False
    else:
        r.raise_for_status()
    
    return False

def upload_file_to_slack(local_file):
    slack_does_not_have_emoji = ensure_slack_does_not_have_emoji()
    if not slack_does_not_have_emoji:
        return False
    with open(local_file, 'rb') as f:
        postBody = {
            'token': slack_token,
            'mode': 'data',
            'name': emoji_name,
        }
        
        files = {'image': f}

        r = requests.post(
            'https://slack.com/api/emoji.add',
            data = postBody,
            files = files
        )
    
    if os.path.exists(local_file):
          os.remove(local_file)

    if(r.ok):
        parsed = json.loads(r.text)
        if parsed['ok']:
            return emoji_name
        else:
            return False
    else:
        # r.raise_for_status() # debug!
        return False;
    
    return False

def get_status_emoji():
    local_file = get_local_file()
    if local_file:
        uploaded_file_to_slack = upload_file_to_slack(local_file)
        if uploaded_file_to_slack:
            return ':' + uploaded_file_to_slack + ':'

    return get_default_status_emoji()

def set_slack_status():
    if current_media_info['artist'] == '' or current_media_info['title'] == '':
        return False
    status_text = 'Now Playing: ' + current_media_info['artist'][:50] + ('...' if len(current_media_info['artist']) > 50 else '') + ' - ' + current_media_info['title']
    status_text = status_text[:97] + ('...' if len(status_text) > 97 else '')

    status_emoji = get_status_emoji()

    # try:
    #     length = metadata['mpris:length'] / 1000000 # comes in as microseconds
    # except:
    #     length = 180 # 3 minutes
    length = 300 # 5 minutes
        
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=length)

    profile = {
        'status_text': status_text,
        'status_emoji': status_emoji,
        'status_expiration': calendar.timegm(expiration_time.timetuple()),
    }

    postBody = {
        'profile': json.dumps(profile),
        'token': slack_token,
    }

    print('[ ] \u001b[36m' + strftime(time_format) + ' - Attempting to set status: \u001b[0m' + status_text + ' \u001b[33m[' + emoji_name + ']\u001b[0m', end='\r')

    r = requests.post(
        'https://slack.com/api/users.profile.set',
        data = postBody
    )

    if(r.ok):
        parsed = json.loads(r.text)
        if parsed['ok']:
            print('[\u001b[32m✓\u001b[0m')
        else:
            print('[\u001b[30m×\u001b[0m')
            print('Error setting status : ' + parsed['error'])
    else:
        r.raise_for_status()

async def get_media_info():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    if current_session:  # there needs to be a media session running
        if current_session.source_app_user_model_id == 'chrome.exe' or current_session.source_app_user_model_id == 'firefox.exe' or current_session.source_app_user_model_id.endswith('.tmp'):
            return previous_media_info
        info = await current_session.try_get_media_properties_async()
        info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
        # pprint.pprint(info_dict) # debug!

        return info_dict

    print('No players playing')
    quit();


try:
    with open("config.json") as config_file:
        config = json.load(config_file)
except IOError as error:
    print('Unable to read `config.json` file')
    quit();

try:
    slack_token = config['slack-token']
except Exception as error:
    print('Config value `slack-token` not defined in `config.json`')
    quit();

try:
    time_format = config['time-format']
except Exception as error:
    print('Config value `time-format` not defined in `config.json`')
    quit();

try:
    emoji_name = config['emoji-name']
except Exception as error:
    emoji_name = 'my-album-art'

try:
    if slack_token == '':
        raise Exception('empty string')
    if slack_token == 'YOUR_SLACK_TOKEN' :
        raise Exception(slack_token)
except Exception as error:
    print('Invalid value for `slack-token` in `config.json`: ' + str(error))
    quit()

previous_media_info = {
    'artist': '',
    'title': ''
}

while True:
    try:
        current_media_info = asyncio.run(get_media_info())
    except RuntimeError:
        current_media_info = previous_media_info

    if current_media_info['artist'] != previous_media_info['artist'] or current_media_info['title'] != previous_media_info['title']:
        previous_media_info = current_media_info
        set_slack_status()

    try:
        sleep(5)
    except KeyboardInterrupt:
        quit()
