import os
import sys
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from collision.collidable import Collidable
from enemys.buran_enemy import BuranEnemy
from initializations.enemy_waves import get_enemy_registry, near_space_waves


class BuranEnemyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1920, 1080))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_collision_tracks_sprite_for_both_directions_and_rotations(self):
        for flipped in (False, True):
            enemy = BuranEnemy(patterns=[], flip_x=flipped)
            self.addCleanup(enemy.destroy)
            enemy.position = pygame.Vector2(900, 500)
            for angle in (0, 45, 90, 180, 270):
                with self.subTest(flipped=flipped, angle=angle):
                    enemy._rotation = angle
                    enemy.scale(enemy.SCALE)
                    enemy.flip_sprite()
                    enemy.rotate()
                    enemy.align_rect()
                    enemy._collider_vertices = enemy.get_rotated_vertices()
                    # Pontos do corpo, nariz e cauda; mais um ponto transparente.
                    for pixel, expected in (((210, 215), True), ((70, 232), True),
                                            ((390, 145), True), ((210, 320), False)):
                        local = (pygame.Vector2(pixel) - pygame.Vector2(214.5)) * (600 / 429)
                        if flipped:
                            local.x = -local.x
                        point = enemy.position + local.rotate(-angle)
                        probe = Collidable()
                        probe._collider_vertices = [point + offset for offset in
                            (pygame.Vector2(-1, -1), pygame.Vector2(1, -1),
                             pygame.Vector2(1, 1), pygame.Vector2(-1, 1))]
                        self.assertEqual(probe.collide_with(enemy), expected)
                        image_point = point - pygame.Vector2(enemy._rect.topleft)
                        alpha = enemy._image.get_at((int(image_point.x), int(image_point.y))).a
                        self.assertEqual(alpha > 0, expected)

    def test_collider_is_convex_and_available_before_first_update(self):
        enemy = BuranEnemy(patterns=[])
        self.addCleanup(enemy.destroy)
        vertices = enemy._collider_vertices
        self.assertGreater(len(vertices), 2)
        turns = [(vertices[(i + 1) % len(vertices)] - vertex).cross(
            vertices[(i + 2) % len(vertices)] - vertices[(i + 1) % len(vertices)])
            for i, vertex in enumerate(vertices)]
        self.assertTrue(all(turn > 0 for turn in turns) or all(turn < 0 for turn in turns))

    def test_flybys_enter_and_leave_with_entire_sprite_off_screen(self):
        registry = get_enemy_registry()
        wave = next(wave for wave in near_space_waves() if wave.spawns[0].enemy == "buran")
        screen = pygame.Rect(0, 0, 1920, 1080)
        for index, spawn in enumerate(wave.spawns):
            with self.subTest(index=index):
                enemy = registry.create(spawn)
                self.addCleanup(enemy.destroy)
                pattern = enemy._patterns[0]
                expected_margin = enemy.SCALE / 2 + 180
                self.assertAlmostEqual(abs(pattern.start.x - (0 if index % 2 == 0 else 1920)),
                                       expected_margin)
                self.assertFalse(enemy._rect.colliderect(screen))
                enemy.update(pattern.warning + (pattern.duration - pattern.warning) / 2)
                self.assertGreaterEqual(enemy._rect.left, screen.left)
                self.assertLessEqual(enemy._rect.right, screen.right)
                enemy.update(pattern.duration)
                self.assertFalse(enemy._rect.colliderect(screen))
                self.assertAlmostEqual(enemy.position.x, pattern.end.x)
                if index + 1 < len(wave.spawns):
                    next_spawn = wave.spawns[index + 1]
                    self.assertGreaterEqual(next_spawn.delay, spawn.delay + pattern.duration)


if __name__ == "__main__":
    unittest.main()
