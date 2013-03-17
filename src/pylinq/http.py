# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.websocket

from pylinq.game import *
import traceback
import os

from functools import wraps

settings = {
    'debug': True, 
    'static_path': os.path.join(os.path.dirname(__file__), '..', '..', 'static')
}

def requires_player(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        self.get_argument('player_name')
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
            self.write({'error': exc.message})
        
        self.finish()

class PlayerJoinHandler(BaseRequestHandler):
    @requires_player
    def post(self):
        response = {}
        player_name = self.get_argument('player_name')
        new_player = self.game.add_player(player_name)
    
        if new_player is self.game.master_player:
            response['is_master'] = True
            
        response['joined'] = True
        
        self.write(response)
        
class PlayerListHandler(BaseRequestHandler):
    def get(self):
        self.write({'player_list': self.game.get_player_standings()})
        
class GameStartHandler(BaseRequestHandler):
    @requires_player
    def post(self):
        self.game.start(self.get_argument('player_name'))
        
class EventSocketHandler(BaseHandler, tornado.websocket.WebSocketHandler):
    def open(self):
        print 'Websocket opened'
        self.game.bind('new_player', self.on_new_player)
        
    def on_message(self, message):
        pass
        
    def on_new_player(self, new_player):
        self.write_message({'event': 'new_player', 'name': new_player.name})
        
    def on_close(self):
        print 'WebSocket closed'

def main():
    game = Game()
    app = tornado.web.Application([
       (r'/join',                   PlayerJoinHandler),
       (r'/player_list',            PlayerListHandler),
       (r'/start',                  GameStartHandler),
       (r'/socket',                 EventSocketHandler),
       (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': settings['static_path']})
    ], settings)
    app.game = game
    
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
