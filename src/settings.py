import os

PORT = 8888
TORNADO_SETTINGS = {
    'debug': True,
    'logging': 'debug',
    'static_path': os.path.join(os.path.dirname(__file__), '..', 'static')
}

ENV = 'dev'


def get_game_setting(key):
    if ENV in GAME:
        settings = GAME[ENV]
    else:
        settings = GAME['default']

    return settings.get(key, None)

GAME = {
    'dev': {
        'min_player_count': 2
    },
    'default': {
        'min_player_count': 4
    }
}
