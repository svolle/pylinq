# -*- coding: utf-8 -*-

IS_SPY = 0
IS_COUNTER_SPY = 1
MAX_PLAYER_NAME_LENGTH = 12


class PlayerException(Exception):
    pass


class Player(object):
    def __init__(self, name):
        if name is '':
            raise PlayerException('Player name cannot by empty')
        elif len(name) > MAX_PLAYER_NAME_LENGTH:
            raise PlayerException(
                'Max player name length is {0}, was {1}'.format(
                    MAX_PLAYER_NAME_LENGTH, len(name)))

        self.name = name
        self.score = 3
        self.role = None
        self.words = []

        self.secret_word = None

    def __repr__(self):
        return 'Player "{0}"'.format(self.name)

    def add_word(self, word):
        if self.secret_word is not None and word == self.secret_word:
            raise PlayerException(
                """
                Player "{0}" picked their own secret word: "{1}"
                """.format(self.name, self.secret_word)
            )

        if len(self.words) is 2:
            raise PlayerException(
                """
                Player "{0}" has already picked their two words: "{1}" and "{2}"
                """.format(
                self.name,
                self.words[0],
                self.words[1]))

        self.words.append(word)

    def get_words(self):
        return self.words

    def make_spy(self, secret_word):
        self.role = IS_SPY
        self.secret_word = secret_word

    def make_counter_spy(self):
        self.role = IS_COUNTER_SPY
        self.secret_word = None

    def is_spy(self):
        return self.role is IS_SPY
