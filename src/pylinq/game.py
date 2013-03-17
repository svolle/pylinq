# -*- coding: utf-8 -*-
from __future__ import print_function
from random import shuffle

from pylinq.utils.observable import Observable
from pylinq.player import Player

MIN_PLAYER_COUNT = 4
MAX_PLAYER_COUNT = 8
SPIES_COUNT = 2

class GameException(Exception):
    pass

class Game(Observable):

    def __init__(self):
        self.players = {}
        self.master_player = None
        self.started = False
        
        super(Game, self).__init__()
        self.add_events('started',
                        'game_finished',
                        'game_aborted',
                        'new_player',
                        'new_round',
                        'player_picked_word',
                        'player_picked_spy',
                        'round_resolved',
                        )
        
    def add_player(self, player_name):
        if self.started:
            raise GameException('The game is already started')
        if len(self.players) is MAX_PLAYER_COUNT:
            raise GameException('Max player count is %d' % MAX_PLAYER_COUNT)
        
        if self.players.get(player_name, None) is not None:
            raise GameException(u'Player name already in use "{0}"'.format(player_name))
        
        new_player = Player(player_name)
        self.players[player_name] = new_player
        if self.master_player is None:
            self.master_player = new_player
        
        self.trigger('new_player', new_player)
        
        return new_player
    
    def get_player_count(self):
        return len(self.players.keys())
    
    def start(self, player_name):
        if self.started:
            raise GameException('The game is already started')
        
        if len(self.players) < MIN_PLAYER_COUNT:
            raise GameException('Minimum player count is %d' % MIN_PLAYER_COUNT)
        
        if player_name != self.master_player.name:
            raise GameException(u'Game can only be started by master player "{0}"'.format(self.master_player.name))
        
        self.started = True
        self.assign_player_roles()
        
        self.trigger('started')
        
    def player_picks_word(self, player_name, word):
        player = self.players[player_name]
        player.add_word(word)
        self.trigger('player_picked_word', player, word)
        
    def abort(self):
        self.trigger('game_aborted')
        self.clean_up()
    
    def clean_up(self):
        self.players = {}
        self.started = False
        
    def assign_player_roles(self):
        roles = list('?' * (len(self.players) - SPIES_COUNT) + 'SS')
        shuffle(roles)
        
        for index, player_name in enumerate(self.players):
            player = self.players[player_name]
            if roles[index] is 'S':
                player.make_spy()
            else:
                player.make_counter_spy()
    
    def get_player_standings(self):
        return dict((p.name, p.score) for p in self.players.values())
