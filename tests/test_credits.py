import os
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game import Game
from game_consts import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.credits import Credits, STAGES, TEAM


class CreditsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_assets_scroll_and_landing_finish(self):
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
        self.assertAlmostEqual(credits.offset, Credits.SPEED * (.5 + .5 * Credits.FAST_MULTIPLIER))
        credits.offset = credits.finish_offset - 1
        credits.update(1)
        self.assertEqual(credits.offset, credits.finish_offset)
        finished.assert_not_called()
        credits.draw(screen)
        self.assertEqual(screen.get_at((0, 0))[:3], (0, 0, 0))
        self.assertEqual(credits.mars.get_width(), SCREEN_WIDTH)
        credits.offset = credits.finish_offset - 400
        credits.draw(screen)
        self.assertNotEqual(screen.get_at((SCREEN_WIDTH // 2, 100))[:3], (0, 0, 0))
        credits.offset = credits.finish_offset
        credits.update(30, fast=True)
        self.assertEqual(credits.offset, credits.finish_offset)
        finished.assert_not_called()

        credits.ship.position.update(credits.mars_rect.centerx,
                                     credits.mars_rect.top + credits.mars_rect.height // 3)
        credits.update(0)
        finished.assert_called_once_with()
        credits.update(1)
        finished.assert_called_once_with()

        smaller = Credits(Mock(), (1280, 720))
        smaller.draw(pygame.Surface((1280, 720)))
        self.assertGreater(smaller.margin, 0)

    def test_shortcut_only_in_menu_and_game_completion_opens_credits(self):
        game = Game.__new__(Game)
        game.screen = pygame.display.get_surface()
        game.current_scene = "menu"
        game.change_scene_to = Game.change_scene_to.__get__(game)
        for modifiers in (0, pygame.KMOD_CTRL, pygame.KMOD_SHIFT):
            Game.handle_keydown(game, pygame.K_c, modifiers)
            self.assertEqual(game.current_scene, "menu")

        shortcut = pygame.KMOD_CTRL | pygame.KMOD_SHIFT
        Game.handle_keydown(game, pygame.K_c, shortcut)
        self.assertEqual(game.current_scene, "credits")
        self.assertFalse(game.credits_from_game)
        Game.return_to_menu(game)
        self.assertEqual(game.current_scene, "menu")

        game.current_scene = "game"
        Game.handle_keydown(game, pygame.K_c, shortcut)
        self.assertEqual(game.current_scene, "game")
        game.campaign_completed = False
        Game.game_completed(game)
        self.assertEqual(game.current_scene, "credits")
        self.assertTrue(game.credits_from_game)

    def test_ship_moves_without_affecting_scroll_or_stage_content(self):
        credits = Credits(Mock())
        keys = defaultdict(bool)
        start = credits.ship.position.copy()
        keys[pygame.K_d] = True
        keys[pygame.K_w] = True
        credits.update(.1, keys=keys)
        self.assertGreater(credits.ship.position.x, start.x)
        self.assertLess(credits.ship.position.y, start.y)
        self.assertAlmostEqual(credits.offset, Credits.SPEED * .1)

        keys.clear()
        keys[pygame.K_LEFT] = True
        credits.update(.5, keys=keys)
        self.assertLess(credits.ship.velocity.x, 0)
        self.assertAlmostEqual(credits.offset, Credits.SPEED * .6)

        for _ in range(30):
            credits.update(.1, keys=keys)
        self.assertGreaterEqual(credits.ship.position.x, credits.ship.size / 2)
        self.assertEqual(credits.ship.velocity.x, 0)

        self.assertTrue(all(not path.startswith("assets/scenery/")
                            for stage in STAGES for path, *_ in stage.sprites))
        self.assertTrue(all(path != "assets/player/foguete-chamas.png"
                            for stage in STAGES for path, *_ in stage.sprites))
        buran = credits.frames["assets/enemys/buran.png"][0]
        drone = credits.frames["assets/enemys/drone_animation.png"][0]
        self.assertGreater(buran.get_width(), drone.get_width() * 7)
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        credits.draw(screen)
        self.assertEqual(screen.get_at((0, 0))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
