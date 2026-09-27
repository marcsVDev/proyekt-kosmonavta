import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from game import Game
from events.event_bus import EventBus
from events.events import Events
from initializations.enemy_waves import get_enemy_registry
from entities.scrollers.infinite_vertical_scroller import InfiniteVerticalScroller
from game_consts import BACKGROUND_MUSIC_PATH, BOSS_MUSIC_PATH, SCREEN_HEIGHT, SCREEN_WIDTH
from system.wave_system import WaveSystem
from util.progresssion import Progression
from util.run_state import RunState
from util.scene import Scene


class GameNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_game(self, current_scene):
        game = Game.__new__(Game)
        game.current_scene = current_scene
        game.play = Mock()
        game.return_to_menu = Mock()
        return game

    def test_enter_and_keypad_enter_play_only_from_menu(self):
        game = self.make_game("menu")
        game.handle_keydown(pygame.K_RETURN)
        game.handle_keydown(pygame.K_KP_ENTER)
        self.assertEqual(game.play.call_count, 2)
        game.current_scene = "game"
        game.handle_keydown(pygame.K_RETURN)
        self.assertEqual(game.play.call_count, 2)

    def test_escape_returns_only_from_game(self):
        game = self.make_game("game")
        game.handle_keydown(pygame.K_ESCAPE)
        game.return_to_menu.assert_called_once_with()
        game.current_scene = "menu"
        game.handle_keydown(pygame.K_ESCAPE)
        game.return_to_menu.assert_called_once_with()

    def test_completed_game_opens_credits_and_escape_returns_to_menu(self):
        game = self.make_game("game")
        game.campaign_completed = False
        game.show_credits = Mock()

        game.game_completed()
        self.assertTrue(game.campaign_completed)
        game.show_credits.assert_called_once_with()
        game.game_completed()
        game.show_credits.assert_called_once_with()
        game.current_scene = "credits"
        game.handle_keydown(pygame.K_ESCAPE)
        game.return_to_menu.assert_called_once_with()

    def test_ctrl_shift_p_skips_dialogues_without_returning_to_menu(self):
        game = self.make_game("game")
        scene = Mock()
        game.scenes = {"game": scene}
        for modifier in (0, pygame.KMOD_CTRL, pygame.KMOD_SHIFT):
            game.handle_keydown(pygame.K_p, modifier)
        scene.skip_dialogues.assert_not_called()
        for modifier in (pygame.KMOD_LCTRL | pygame.KMOD_LSHIFT,
                         pygame.KMOD_RCTRL | pygame.KMOD_RSHIFT):
            game.handle_keydown(pygame.K_p, modifier)
        self.assertEqual(scene.skip_dialogues.call_count, 2)
        game.return_to_menu.assert_not_called()

        scene.skip_dialogues.reset_mock()
        game._pending_phase = object()
        game.handle_keydown(pygame.K_p, pygame.KMOD_CTRL | pygame.KMOD_SHIFT)
        game.current_scene = "menu"
        game._pending_phase = None
        game.handle_keydown(pygame.K_p, pygame.KMOD_CTRL | pygame.KMOD_SHIFT)
        scene.skip_dialogues.assert_not_called()
        game.return_to_menu.assert_not_called()

    def test_ctrl_shift_o_toggles_god_mode_and_updates_player(self):
        game = self.make_game("game")
        game.god_mode = False
        player = SimpleNamespace(god_mode=False)
        game.scenes = {"game": SimpleNamespace(player=player)}
        combo = pygame.KMOD_CTRL | pygame.KMOD_SHIFT

        game.handle_keydown(pygame.K_o, pygame.KMOD_CTRL)
        self.assertFalse(game.god_mode)
        game.handle_keydown(pygame.K_o, combo)
        self.assertTrue(game.god_mode)
        self.assertTrue(player.god_mode)
        game.handle_keydown(pygame.K_o, combo)
        self.assertFalse(game.god_mode)
        self.assertFalse(player.god_mode)

    def test_return_clears_scene_and_resets_systems(self):
        game = Game.__new__(Game)
        game.current_scene = "game"
        game.change_scene_to = Game.change_scene_to.__get__(game)
        waves, progression = Mock(), Mock()
        scene = Mock()
        scene.get_system.side_effect = lambda name, kind: waves if name == "waves" else progression
        game.scenes = {"game": scene, "menu": Mock()}
        Game.return_to_menu(game)
        scene.clear_scene.assert_called_once_with()
        waves.reset.assert_called_once_with()
        progression.reset.assert_called_once_with()
        self.assertEqual(game.current_scene, "menu")

    @patch("game.pygame.mixer.music")
    def test_background_music_loops_at_configured_volume(self, music):
        game = Game.__new__(Game)
        game.start_background_music()
        music.load.assert_called_once()
        music.set_volume.assert_called_once_with(Game.BACKGROUND_MUSIC_VOLUME)
        music.play.assert_called_once_with(-1)

    def test_phase_transition_waits_on_black_frame_before_loading(self):
        game = Game.__new__(Game)
        game._pending_phase = None
        game._phase_transition_remaining = 0
        game.load_phase = Mock()
        phase = SimpleNamespace(name="Estratosfera")

        game.begin_phase_transition(phase)
        game.update_phase_transition(.75)
        game.load_phase.assert_not_called()
        self.assertTrue(game.phase_transition_active)
        game.update_phase_transition(.25)
        game.load_phase.assert_called_once_with(phase)
        self.assertFalse(game.phase_transition_active)

    @patch("game.pygame.mixer.music")
    def test_boss_music_replaces_ambient_and_does_not_restart_needlessly(self, music):
        game = Game.__new__(Game)
        game._current_music_path = BACKGROUND_MUSIC_PATH

        game.play_music(BACKGROUND_MUSIC_PATH)
        music.load.assert_not_called()
        game.play_music(BOSS_MUSIC_PATH)
        music.load.assert_called_once_with(BOSS_MUSIC_PATH)
        music.play.assert_called_once_with(-1)

    def test_infinite_scroller_covers_viewport_and_wraps_after_long_frame(self):
        image = pygame.Surface((100, 100))
        image.fill((10, 20, 30))
        scroller = InfiniteVerticalScroller(image, velocity=500, running=True)

        self.assertGreaterEqual(scroller.image.get_width(), SCREEN_WIDTH)
        self.assertGreaterEqual(scroller.image.get_height(), SCREEN_HEIGHT)

        scroller.update(scroller.height * 5 / scroller.velocity + .25)
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.fill((0, 0, 0))
        scroller.draw(screen)
        self.assertEqual(screen.get_at((SCREEN_WIDTH - 1, 0))[:3], (10, 20, 30))
        self.assertEqual(screen.get_at((SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1))[:3], (10, 20, 30))

    def test_launch_completion_changes_phase_without_uninitialized_player(self):
        EventBus.events.clear()
        run_state = RunState()
        scene = Scene(game_scene=True)
        progression = Progression(run_state)
        scene.add_system("progression", progression)
        scene.add_system("waves", WaveSystem(scene, get_enemy_registry()))
        scene.add_system("boss", Mock(update=Mock(), reset=Mock()))

        game = Game.__new__(Game)
        game.scenes = {"game": scene}
        game.god_mode = False
        game.run_state = run_state
        EventBus.connect(Events.PHASE_CHANGED, game.load_phase)
        progression.game_started()
        game.load_phase(progression.phases[0])
        self.assertIsNone(scene.player)
        self.assertNotIn("player", scene.blackboard)

        scene.get_entity("launch_animation", object).run()
        scene.run(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)), 6, [])

        self.assertEqual(progression.phase_index, 1)
        self.assertIs(scene.player, progression.phases[1].default_entities["player"])
        self.assertTrue(hasattr(scene.player, "_rect"))
        scene.clear_scene()
        EventBus.events.clear()


if __name__ == "__main__":
    unittest.main()
