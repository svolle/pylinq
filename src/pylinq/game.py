# -*- coding: utf-8 -*-
from __future__ import print_function
from random import shuffle
import settings
import logging


from pylinq.utils.observable import Observable
from pylinq.player import Player
from pylinq.event import Events

MIN_PLAYER_COUNT = settings.get_game_setting('min_player_count')
MAX_PLAYER_COUNT = 8
SPIES_COUNT = 2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GameException(Exception):
    pass


class GameState(Observable):
    """
    Stores and handles pretty much of the game state.
    Most of the methods affecting the game state in some will trigger
    an event accordingly.
    """

    def __init__(self):
        self.players = {}
        self._master_player = None
        self.started = False
        self.round_played = 0

        super(GameState, self).__init__()
        self.add_events(Events.GAME_STARTED,
                        Events.GAME_FINISHED,
                        Events.GAME_ABORTED,
                        Events.NEW_PLAYER,
                        Events.NEW_MASTER,
                        Events.PLAYER_QUIT,
                        Events.NEW_ROUND,
                        Events.PLAYER_PICKED_WORD,
                        Events.PLAYER_ROLE_ASSIGNED,
                        Events.ROUND_RESOLVED,
                        )

    @property
    def master_player(self):
        """
        The master player is the first to join the game, or the next in line
        in case the master leaves. The master player is the only one allowed to
        start the game and the subsequent rounds.
        """
        return self._master_player

    @master_player.setter
    def master_player(self, player):
        self._master_player = player

        if player is not None:
            self.trigger(Events.NEW_MASTER, player)

    def add_player(self, player_name):
        """
        Add a player to the game by their name and elect them master if
        needed.
        """
        if self.started:
            raise GameException('The game is already started')
        if len(self.players) is MAX_PLAYER_COUNT:
            raise GameException('Max player count is %d' % MAX_PLAYER_COUNT)

        if self.players.get(player_name, None) is not None:
            raise GameException(
                'Player name already in use "{}"'.format(player_name))

        new_player = Player(player_name)
        self.players[player_name] = new_player
        if self.master_player is None:
            self.master_player = new_player

        self.trigger(Events.NEW_PLAYER, new_player)
        logger.info('New player joined: "{}"'.format(player_name))

        return new_player

    def remove_player(self, player_name):
        """
        Remove a player from the game and elects a new master if the quitter
        is master.
        """
        logger.info('Player "{}" quit the game'.format(player_name))

        if self.started:
            self.abort()
        else:
            quitter = self.players[player_name]
            del self.players[player_name]
            self.trigger(Events.PLAYER_QUIT, quitter)

            if len(self.players) > 0:
                if self.master_player is quitter:
                    self.master_player = next(iter(self.players.values()))
            else:
                self.master_player = None

    def get_player_count(self):
        """
        Get number of players in the game
        """
        return len(self.players)

    def start(self, player_name):
        """
        Start the game. Fails if the required amount of players is not met
        or if the game is already started.
        """
        if self.started:
            raise GameException('The game is already started')

        if len(self.players) < MIN_PLAYER_COUNT:
            raise GameException('Minimum player count is %d' % MIN_PLAYER_COUNT)

        if player_name != self.master_player.name:
            raise GameException(
                'Game can only be started by master player "{}"'.format(
                    self.master_player.name))

        self.started = True

        self.trigger(Events.GAME_STARTED)
        logger.info(u'Game started by player "{}"'.format(player_name))

        self.assign_player_roles()

    def player_picks_word(self, player_name, word):
        """
        Set the word the player picked for the round.
        """
        player = self.players[player_name]
        player.add_word(word)
        self.trigger(Events.PLAYER_PICKED_WORD, player, word)

    def abort(self):
        """
        Abort the game.
        """
        self.clean_up()

        self.trigger(Events.GAME_ABORTED)
        logger.info('Game aborted')

    def clean_up(self):
        """
        Clean up game state.
        """
        self.players = {}
        self.started = False
        self.master_player = None
        self.round_played = 0

    def assign_player_roles(self):
        """
        Randomly assign roles to the players in the game.
        """
        roles = list('?' * (len(self.players) - SPIES_COUNT) + 'SS')
        shuffle(roles)

        for index, player_name in enumerate(self.players):
            player = self.players[player_name]
            if roles[index] is 'S':
                player.make_spy()
            else:
                player.make_counter_spy()

            self.trigger(
                Events.PLAYER_ROLE_ASSIGNED,
                player
            )

    def get_player_standings(self):
        """
        Get player standings (score) in the game
        """
        return [
            {'name': p.name, 'score': p.score} for p in self.players.values()
        ]
