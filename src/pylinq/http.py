# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver

import logging
import json
import functools
import signal
import time

from pylinq.game import *
from pylinq.event import Events
import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

server_stopping = False


# Decorator for handlers requiring a player name argument
def requires_player(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self.player_name = self.get_argument('player_name')
        return fn(self, *args, **kwargs)

    return wrapper


class BaseHandler(object):
    @property
    def game(self):
        return self.application.game


class BaseRequestHandler(BaseHandler, tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        if 'exc_info' in kwargs:
            exc_type, exc, _ = kwargs['exc_info']

            if exc_type is GameException:
                self.set_status(400)
                self.write({'error': str(exc)})

        self.finish()


class PlayerJoinHandler(BaseRequestHandler):
    @requires_player
    def post(self):
        self.game.add_player(self.player_name)
        self.write({'joined': True})


class PlayerQuitHandler(BaseRequestHandler):
    @requires_player
    def post(self):
        response = {}

        self.game.remove_player(self.player_name)
        response['quit'] = True
        self.write(response)


class PlayerListHandler(BaseRequestHandler):
    def get(self):
        self.write(json.dumps(self.game.get_player_standings()))


class GameStartHandler(BaseRequestHandler):
    @requires_player
    def post(self):
        self.game.start(self.player_name)
        self.write({'started': True})


class EventSocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):

    # Keeps track of open websocket client connections
    openEventSocketClients = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = None

    def open(self):
        logger.debug('New websocket opened: {}'.format(self))
        self.game.bind(Events.NEW_PLAYER,
                       self.on_new_player)
        self.game.bind(Events.NEW_MASTER,
                       self.on_new_master)
        self.game.bind(Events.PLAYER_QUIT,
                       self.on_player_quit)
        self.game.bind(Events.GAME_STARTED,
                       self.on_game_started)
        self.game.bind(Events.GAME_ABORTED,
                       self.on_game_aborted)
        self.game.bind(Events.PLAYER_ROLE_ASSIGNED,
                       self.on_player_role_assigned)

        EventSocketHandler.openEventSocketClients.append(self)

    def on_message(self, message):
        message = json.loads(message, encoding='utf-8')
        if 'playerName' in message \
                and message['playerName'] in self.game.players:
            self.player = self.game.players[message['playerName']]

    def on_new_player(self, new_player):
        self.write_message({
            'event': Events.NEW_PLAYER,
            'player': {
                'name': new_player.name,
                'score': new_player.score
            }
        })

    def on_new_master(self, new_master):
        self.write_message({
            'event': Events.NEW_MASTER,
            'player_name': new_master.name
        })

    def on_player_quit(self, quitter):
        self.write_message({
            'event': Events.PLAYER_QUIT,
            'player_name': quitter.name
        })

    def on_game_started(self):
        self.write_message({'event': Events.GAME_STARTED})

    def on_game_aborted(self):
        self.write_message({'event': Events.GAME_ABORTED})

    def on_close(self):
        logger.debug('Websocket closed: {}'.format(self))
        self.game.unbind(Events.NEW_PLAYER,      self.on_new_player)
        self.game.unbind(Events.NEW_MASTER,      self.on_new_master)
        self.game.unbind(Events.PLAYER_QUIT,     self.on_player_quit)
        self.game.unbind(Events.GAME_STARTED,    self.on_game_started)
        self.game.unbind(Events.GAME_ABORTED,    self.on_game_aborted)

        if self in EventSocketHandler.openEventSocketClients:
            EventSocketHandler.openEventSocketClients.remove(self)

        if self.game.started:
            map(lambda s: s.write_message({'event': Events.LOST_CONNECTION}),
                EventSocketHandler.openEventSocketClients)

    def on_player_role_assigned(self, player):
        if player is self.player:
            self.write_message({
                'event': Events.PLAYER_ROLE_ASSIGNED,
                'role': player.role,
                'secret_word': player.secret_word
            })


class StaticFileHandler(tornado.web.StaticFileHandler):
    def get(self, *args, **kwargs):
        super().get(*args, **kwargs)
        self.set_header('Cache-Control', 'no-cache')

routes = [
    (r'/',                       tornado.web.RedirectHandler,
        {"url": '/static/index.html'}),
    (r'/join',                   PlayerJoinHandler),
    (r'/quit',                   PlayerQuitHandler),
    (r'/players',                PlayerListHandler),
    (r'/start',                  GameStartHandler),
    (r'/socket',                 EventSocketHandler),
    (r'/static/(.*)',            StaticFileHandler, {
        'path': settings.TORNADO_SETTINGS['static_path']
    })
]


def main():
    app = tornado.web.Application(routes, settings.TORNADO_SETTINGS)
    game = GameState()
    app.game = game

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(settings.PORT)

    io_loop = tornado.ioloop.IOLoop.instance()

    # Handle graceful shutdown
    def sig_handler(sig, *args):
        global server_stopping
        logger.warning('Caught signal: {}'.format(sig))

        if not server_stopping:
            server_stopping = True
            tornado.ioloop.IOLoop.instance().add_callback_from_signal(shutdown)

    def shutdown():
        logger.info('Shutting down...')
        game.abort()
        http_server.stop()

        def poll_stop():
            remaining = len(io_loop._handlers)

            # Wait until we only have only one IO handler remaining.  That
            # final handler will be our PeriodicCallback polling task.
            if remaining is 1:
                io_loop.stop()
            else:
                logger.info('[%d] Waiting on IO handlers (%d remaining)',
                            tornado.process.task_id() or 0, remaining)

        # Cleanly close websocket client connections
        for client in EventSocketHandler.openEventSocketClients:
            try:
                client.close()
            except:
                # Websocket could or could not be there
                pass

        # Poll the IO loop's handlers until they all shut down.
        poller = tornado.ioloop.PeriodicCallback(poll_stop, 250,
                                                 io_loop=io_loop)
        poller.start()

        # Give up after 10 seconds of waiting.
        io_loop.add_timeout(time.time() + 10, io_loop.stop)

    signal.signal(signal.SIGINT,  sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    io_loop.start()
    logger.info('Exit')

if __name__ == '__main__':
    main()
