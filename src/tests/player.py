import unittest

from pylinq.player import *


class PlayerTestCase(unittest.TestCase):
    def setUp(self):
        self.player = Player('gontran')

    # def test_bad_player_names(self):
    #     self.assertRaises(PlayerException, Player, '')
    #     self.assertRaises(PlayerException, Player,  '?' * 13)

    # def test_add_words(self):
    #     self.player.add_word('spam')
    #     self.player.add_word('bogus')

    #     self.assertEqual(self.player.get_words(), ['spam', 'bogus'])
    #     self.assertRaises(PlayerException, self.player.add_word, 'eggs')

    # def test_roles(self):
    #     self.player.make_spy()
    #     self.assertTrue(self.player.is_spy())
    #     self.player.make_counter_spy()
    #     self.assertFalse(self.player.is_spy())
