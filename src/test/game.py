import unittest
from pylinq.game import *
from pylinq.player import Player
from mock import Mock
from random import Random

class GameTest(unittest.TestCase):

    def setUp(self):
        self.game = Game()

    def test_add_player(self):
        foo = self.game.add_player('foo')
        self.assertIsInstance(foo, Player)
        self.assertIs(self.game.players['foo'], foo)
        
        for i in range(0,7):
            self.game.add_player('bar-%d' % i)
            
        self.assertRaises(GameException, self.game.add_player, 'spam')
        
    def test_player_picks_word(self):
        foo = self.game.add_player('foo')
        foo.add_word = Mock()
        self.game.player_picks_word('foo', 'bar')
        foo.add_word.assert_called_with('bar')
        
    def test_assign_roles(self):
        for i in range(0,7):
            self.game.add_player('bar-%d' % i)
        
        self.game.assign_player_roles()
            
        for player in self.game.players.values():
            self.assertIsNotNone(player.role)
            
        
    def test_start(self):
        for i in range(0,7):
            self.game.add_player('bar-%d' % i)
        
        self.game.start('bar-0')
        self.assertTrue(self.game.started)
        
    def test_start_when_already_started(self):
        for i in range(0,7):
            self.game.add_player('bar-%d' % i)
        
        self.game.start('bar-0')
        self.assertRaises(GameException, self.game.start, 'bar-0')
        
    def test_start_with_non_master_player(self):
        for i in range(0,7):
            self.game.add_player('bar-%d' % i)
        
        self.assertRaises(GameException, self.game.start, 'bar-1')
        
        
    def test_add_player_when_game_already_started(self):
        for i in range(0, 4):
            self.game.add_player('bar-%d' % i)
            
        self.game.start('bar-0')
        self.assertRaises(GameException, self.game.add_player, 'spam')
        
    def test_add_player_name_already_present(self):
        self.game.add_player('foo')
        self.assertRaises(GameException, self.game.add_player, 'foo')
        
    def test_get_player_count(self):
        self.assertEqual(self.game.get_player_count(), 0)
        random_count = Random().randint(1, 7)
        
        for i in range(0, random_count):
            self.game.add_player('foo-%s' % i)
            
        self.assertEqual(self.game.get_player_count(), random_count)
        
    def test_player_standings(self):
        foo  = self.game.add_player('foo')
        bar  = self.game.add_player('bar')
        spam = self.game.add_player('spam')
        
        foo.score  = 12
        bar.score  = 100
        spam.score = 7
        
        self.assertDictEqual(self.game.get_player_standings(), {'foo': 12, 'bar': 100, 'spam': 7})
        
    def test_abort(self):
        self.game.abort()
        self.assertFalse(self.game.started)
        self.assertEqual(len(self.game.players.keys()), 0)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()