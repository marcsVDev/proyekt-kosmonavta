import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game import Game
from game_consts import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.credits import Credits, CreditsMenuButton, STAGES, TEAM


class CreditsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_assets_scroll_and_natural_finish(self):
        finished = Mock()
        credits = Credits(finished)
        self.assertEqual(len(credits.cards), len(STAGES) + 2)
        self.assertEqual(len(TEAM), 4)
        self.assertTrue(all(len(credits.frames[path]) >= 1 for stage in STAGES
                            for path, *_ in stage.sprites))
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for index in range(len(credits.cards)):
            credits.offset = -credits.tops[index] + 120
            credits.draw(screen)
        credits.offset = 0
        credits.update(.5)
        self.assertAlmostEqual(credits.offset, Credits.SPEED * .5)
        credits.update(.5, fast=True)
        self.assertAlmostEqual(credits.offset, Credits.SPEED * 2.5)
        credits.offset = credits.finish_offset - 1
        credits.update(1)
        finished.assert_called_once_with()

        smaller = Credits(Mock(), (1280, 720))
        smaller.draw(pygame.Surface((1280, 720)))
        self.assertGreater(smaller.margin, 0)

    def test_menu_and_game_open_credits(self):
        game = Game.__new__(Game)
        game.screen = pygame.display.get_surface()
        game.current_scene = "menu"
        game.change_scene_to = Game.change_scene_to.__get__(game)
        Game.handle_keydown(game, pygame.K_c)
        self.assertEqual(game.current_scene, "credits")
        self.assertFalse(game.credits_from_game)
        Game.return_to_menu(game)
        self.assertEqual(game.current_scene, "menu")

        button = CreditsMenuButton(game.show_credits)
        button.update(0, [pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                            {"button": 1, "pos": button.area.center})])
        self.assertEqual(game.current_scene, "credits")
        Game.return_to_menu(game)
        game.current_scene = "game"
        game.campaign_completed = False
        Game.game_completed(game)
        self.assertEqual(game.current_scene, "credits")
        self.assertTrue(game.credits_from_game)


if __name__ == "__main__":
    unittest.main()
