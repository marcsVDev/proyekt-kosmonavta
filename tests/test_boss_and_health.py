import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from entities.enemy_projectile import EnemyProjectile
from entities.enemy_beam import EnemyBeam
from entities.guided_missile import GuidedMissile
from collision.collidable import Collidable
from entities.player import Player
from enemys.mother_ship_enemy import MotherShipEnemy
from events.event_bus import EventBus
from events.events import Events
from initializations.boss_waves import boss_waves
from initializations.enemy_waves import get_enemy_registry
from initializations.phases import get_phases
from system.boss_fight_system import BossFightSystem
from util.run_state import RunState
from util.scene import Scene


class BossAndHealthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1920, 1080))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        EventBus.events.clear()

    def test_run_state_clamps_resets_and_is_shared_by_every_phase(self):
        state = RunState()
        self.assertEqual(state.health, 10)
        for _ in range(10):
            state.damage()
        self.assertEqual(state.health, 0)
        self.assertTrue(state.is_game_over)
        state.reset()
        self.assertEqual(state.health, 10)
        phases = get_phases(state)
        self.assertTrue(all(phase.default_entities["player"].run_state is state
                            for phase in phases if "player" in phase.default_entities))
        for phase in phases:
            for entity in phase.default_entities.values():
                entity.destroy()

    def test_collision_costs_one_hp_and_invulnerability_blocks_followups(self):
        state = RunState()
        player = Player(state)
        player.update(0)
        sources = [EnemyProjectile(player.position, (0, 0)) for _ in range(3)]
        self.assertTrue(player.take_damage(sources))
        self.assertEqual(state.health, 9)
        self.assertTrue(all(source.to_destroy for source in sources))
        self.assertFalse(player.take_damage((EnemyProjectile(player.position, (0, 0)),)))
        self.assertEqual(state.health, 9)
        player.update(1.51)
        self.assertTrue(player.take_damage((EnemyProjectile(player.position, (0, 0)),)))
        self.assertEqual(state.health, 8)
        player.destroy()

    def test_death_is_emitted_once_and_god_mode_preserves_health(self):
        state = RunState()
        player = Player(state)
        deaths = []
        EventBus.connect(Events.PLAYER_DIED, deaths.append)
        player.god_mode = True
        player.take_damage((object(),))
        self.assertEqual(state.health, 10)
        player.god_mode = False
        for expected in range(9, -1, -1):
            player.invulnerable_remaining = 0
            player.take_damage(())
            self.assertEqual(state.health, expected)
        player.take_damage(())
        self.assertEqual(deaths, [player])

    def test_missile_accelerates_caps_speed_and_limits_turn(self):
        boss = MotherShipEnemy()
        boss.update(3)
        target = pygame.Vector2(0, boss.launch_position.y)
        missile = GuidedMissile(boss.launch_position, lambda: target, boss)
        missile.elapsed = missile.config.telegraph_duration
        before = missile.direction.copy()
        missile.update(.1)
        self.assertLessEqual(abs(before.angle_to(missile.direction)), missile.config.turn_rate * .1 + 1e-6)
        missile.update(20)
        self.assertLessEqual(missile.speed, missile.config.max_speed)
        self.assertTrue(missile.exploded)
        missile.update(.2)
        self.assertTrue(missile.to_destroy)

    def test_missile_takes_short_turn_across_angle_wrap(self):
        boss = MotherShipEnemy()
        missile = GuidedMissile((960, 600), lambda: (860, 590), boss)
        self.addCleanup(missile.destroy)
        missile.state = "seeking"
        missile.direction = pygame.Vector2(-100, 10).normalize()
        desired = pygame.Vector2(-100, -10).normalize()
        before = abs((missile.direction.angle_to(desired) + 180) % 360 - 180)
        missile.update(1 / 120)
        after = abs((missile.direction.angle_to(desired) + 180) % 360 - 180)
        self.assertLess(after, before)

    def test_center_missile_clears_hull_before_it_can_hit_boss(self):
        boss = MotherShipEnemy()
        boss.update(3)
        missile = GuidedMissile(boss.launch_position, lambda: (960, 900), boss)
        self.addCleanup(missile.destroy)
        scene = Scene(True)
        scene.add_entity(boss)
        missile.update(missile.config.telegraph_duration + 1 / 60)
        missile.resolve_collisions(scene)
        self.assertFalse(missile.exploded)
        self.assertEqual(boss.health, boss.max_health)

    def test_armed_missile_can_hit_any_part_of_boss_hull_from_below(self):
        for offset in (-950, -500, -250, 0, 250, 500, 950):
            for fps in (20, 60, 120):
                with self.subTest(offset=offset, fps=fps):
                    boss = MotherShipEnemy()
                    boss.update(3)
                    point = pygame.Vector2(boss.position.x + offset, boss.body_rect.bottom)
                    missile = GuidedMissile(point + (0, 400), lambda: point, boss)
                    self.addCleanup(missile.destroy)
                    missile.state = "seeking"
                    missile.direction = pygame.Vector2(0, -1)
                    missile.flight_time = missile.config.arm_time
                    scene = Scene(True)
                    scene.add_entity(boss)
                    for _ in range(fps * 2):
                        missile.update(1 / fps)
                        missile.resolve_collisions(scene)
                        if missile.exploded:
                            break
                    self.assertEqual(missile.explosion_reason, "boss")
                    self.assertEqual(boss.health, 4)

    def test_boss_collider_reaches_both_sprite_corners(self):
        boss = MotherShipEnemy()
        boss.update(3)
        for x in (boss.body_rect.left + 2, boss.body_rect.right - 2):
            with self.subTest(x=x):
                probe = Collidable()
                y = boss.body_rect.bottom - 5
                probe._collider_vertices = [
                    pygame.Vector2(x - 2, y - 2), pygame.Vector2(x + 2, y - 2),
                    pygame.Vector2(x + 2, y + 2), pygame.Vector2(x - 2, y + 2),
                ]
                self.assertTrue(boss.collide_with(probe))

    def test_boss_blocks_player_without_causing_contact_damage(self):
        scene = Scene(True)
        player = Player(RunState())
        boss = MotherShipEnemy()
        boss.update(3)
        scene.add_entity(player)
        scene.add_entity(boss)
        self.addCleanup(scene.clear_scene)

        player.position.update(boss.position.x, boss.body_rect.bottom + 10)
        player.update(0)
        player.velocity.y = -500
        health = player.run_state.health
        scene.check_collisions()
        self.assertEqual(player.run_state.health, health)
        self.assertAlmostEqual(min(vertex.y for vertex in player._collider_vertices),
                               boss.body_rect.bottom)
        self.assertEqual(player.velocity.y, 0)

        player.position.y = boss.body_rect.bottom + 200
        player.update(0)
        player.position.y = boss.body_rect.top - 200
        player._collider_vertices = player.get_rotated_vertices()
        scene.check_collisions()
        self.assertAlmostEqual(min(vertex.y for vertex in player._collider_vertices),
                               boss.body_rect.bottom)
        self.assertEqual(player.run_state.health, health)

    def test_missile_cannot_damage_boss_before_entry(self):
        boss = MotherShipEnemy()
        point = boss.body_rect.center
        missile = GuidedMissile(point, lambda: point, boss)
        self.addCleanup(missile.destroy)
        missile.state = "seeking"
        missile.flight_time = missile.config.arm_time
        missile.resolve_collisions(Scene(True))
        self.assertEqual(boss.health, boss.max_health)
        self.assertFalse(missile.exploded)

    def test_missile_returns_toward_player_after_dodge(self):
        boss = MotherShipEnemy()
        boss.update(3)
        target = pygame.Vector2(960, 500)
        missile = GuidedMissile((960, 800), lambda: target, boss)
        self.addCleanup(missile.destroy)
        missile.state = "seeking"
        missile.speed = missile.config.max_speed
        scene = Scene(True)
        scene.add_entity(boss)
        for _ in range(120):
            missile.update(1 / 120)
            missile.resolve_collisions(scene)
            if missile.exploded:
                break
        self.assertFalse(missile.exploded)
        self.assertLess(missile.direction.y, 0)
        self.assertLess(missile.position.y, 800)

    def test_missile_motion_is_stable_across_frame_rates(self):
        boss = MotherShipEnemy()
        boss.update(3)
        target = pygame.Vector2(250, 850)

        def simulate(step):
            missile = GuidedMissile(boss.launch_position, lambda: target, boss)
            missile.elapsed = missile.config.telegraph_duration
            elapsed = 0.0
            while elapsed < 2:
                dt = min(step, 2 - elapsed)
                missile.update(dt)
                elapsed += dt
            missile.destroy()
            return missile.position, missile.direction

        fine_position, fine_direction = simulate(1 / 120)
        coarse_position, coarse_direction = simulate(1 / 20)
        self.assertLess(fine_position.distance_to(coarse_position), 1)
        self.assertLess(abs(fine_direction.angle_to(coarse_direction)), .1)

    def test_only_armed_missile_on_hull_damages_boss(self):
        boss = MotherShipEnemy()
        boss.update(3)
        point = pygame.Vector2(boss.position.x, boss.body_rect.bottom)
        missile = GuidedMissile(point, lambda: point, boss)
        missile.state = "seeking"
        scene = Scene(True)
        scene.add_entity(boss)
        missile.resolve_collisions(scene)
        self.assertEqual(boss.health, 5)
        self.assertEqual(missile.explosion_reason, "armor")

        armed = GuidedMissile(point, lambda: point, boss)
        armed.state = "seeking"
        armed.flight_time = armed.config.arm_time
        armed.resolve_collisions(scene)
        self.assertEqual(boss.health, 4)
        self.assertEqual(armed.explosion_reason, "boss")

    def test_unarmed_hull_is_armor_and_missile_can_destroy_laser_ship(self):
        boss = MotherShipEnemy()
        boss.update(3)
        point = pygame.Vector2(boss.position.x, boss.body_rect.bottom)
        scene = Scene(True)
        scene.add_entity(boss)
        closed = GuidedMissile(point, lambda: point, boss)
        closed.state = "seeking"
        closed.resolve_collisions(scene)
        self.assertEqual(boss.health, 5)
        self.assertEqual(closed.explosion_reason, "armor")

        laser_spawn = boss_waves()[2].spawns[0]
        laser = get_enemy_registry().create(laser_spawn, lambda: pygame.Vector2(960, 900))
        laser.position.update(400, 500)
        laser.update(0)
        scene.add_entity(laser)
        missile = GuidedMissile(laser.position, lambda: laser.position, boss)
        missile.state = "seeking"
        missile.flight_time = missile.config.arm_time
        missile.resolve_collisions(scene)
        self.assertTrue(laser.to_destroy)
        self.assertEqual(missile.explosion_reason, "laser_ship")
        scene.clear_scene()

    def test_boss_has_seven_waves_and_loops_from_seven_to_two(self):
        self.assertEqual(len(boss_waves()), 7)
        scene = Scene(True)
        player = Player(RunState())
        player.update(0)
        scene.add_entity(player)
        system = BossFightSystem(scene, get_enemy_registry())
        phase = get_phases(player.run_state)[4]
        system.load_phase(phase)
        system.wave_index = 6
        system._begin_next_wave()
        self.assertEqual(system.wave_index, 1)
        scene.clear_scene()
        for item in phase.default_entities.values():
            item.destroy()

    def test_fifth_valid_hit_defeats_boss_once(self):
        boss = MotherShipEnemy()
        original_image = boss.image
        defeated = []
        EventBus.connect(Events.BOSS_DEFEATED, defeated.append)
        for index in range(5):
            self.assertTrue(boss.take_missile_hit(True))
            self.assertEqual(boss.health, 4 - index)
            self.assertIs(boss.image, boss.damaged_image if boss.health <= 2 else original_image)
        self.assertFalse(boss.take_missile_hit(True))
        self.assertEqual(defeated, [boss])

    def test_boss_explosion_follows_ship_and_is_drawn_above_it(self):
        boss = MotherShipEnemy()
        boss.update(3)
        for _ in range(boss.max_health):
            boss.take_missile_hit()

        screen = Mock()
        boss.draw(screen)
        self.assertEqual(screen.blit.call_args_list[-1].args,
                         (boss.explosion_frames[0], boss.body_rect.topleft))
        self.assertEqual(screen.blit.call_args_list[-2].args[0], boss.image)

        boss.update(boss.config.explosion_frame_duration)
        screen.reset_mock()
        boss.draw(screen)
        self.assertEqual(screen.blit.call_args_list[-1].args,
                         (boss.explosion_frames[1], boss.body_rect.topleft))

        boss.update(boss.config.explosion_frame_duration * (len(boss.explosion_frames) - 1))
        screen.reset_mock()
        boss.draw(screen)
        self.assertEqual(screen.blit.call_args_list[-1].args,
                         (boss.explosion_frames[0], boss.body_rect.topleft))

        boss.update(boss.config.defeat_duration)
        screen.reset_mock()
        boss.draw(screen)
        expected_frame = (int(boss.defeat_elapsed / boss.config.explosion_frame_duration)
                          % len(boss.explosion_frames))
        self.assertEqual(screen.blit.call_args_list[-1].args,
                         (boss.explosion_frames[expected_frame], boss.body_rect.topleft))

    def test_missile_waits_for_pending_spawns_enemies_and_beams(self):
        scene = Scene(True)
        player = Player(RunState())
        scene.add_entity(player)
        self.addCleanup(scene.clear_scene)
        player.time_since_damage = 10
        system = BossFightSystem(scene, get_enemy_registry())
        system.load_phase(SimpleNamespace(boss_fight=True))
        system.intro_remaining = 0
        system._begin_next_wave()
        system.wave_elapsed = 20
        system.pending = [[100, 0, system.waves[0].spawns[0]]]

        def assert_waiting():
            system.update(.1)
            self.assertFalse(system.missile_created)
            self.assertEqual(system.rest_remaining, 0)

        assert_waiting()
        for enemy in system.active_enemies:
            enemy.destroy()
        assert_waiting()  # Future reinforcements still belong to the attack wave.
        system.pending.clear()
        beam = Mock(spec=EnemyBeam, to_destroy=False)
        scene.entities.append(beam)
        assert_waiting()
        beam.to_destroy = True
        system.update(.1)
        self.assertTrue(system.missile_created)
        missile = system.active_missile
        system.update(10)
        self.assertIs(system.active_missile, missile)
        self.assertEqual(system.wave_index, 0)
        self.assertEqual(system.rest_remaining, 0)
        missile.destroy()
        system.update(.1)
        self.assertGreater(system.rest_remaining, 0)

    def test_boss_system_completes_once_after_defeat_animation(self):
        state = RunState()
        scene = Scene(True)
        player = Player(state)
        player.update(0)
        scene.add_entity(player)
        system = BossFightSystem(scene, get_enemy_registry())
        phase = get_phases(state)[4]
        completed = []
        EventBus.connect(Events.PHASE_COMPLETED, completed.append)
        system.load_phase(phase)
        for _ in range(5):
            system.boss.take_missile_hit(True)
        system.update(4.1)
        system.update(4.1)
        self.assertEqual(completed, [phase])
        self.assertTrue(system.completed)
        scene.clear_scene()
        for entity in phase.default_entities.values():
            entity.destroy()

    def test_player_death_cancels_boss_spawns(self):
        state = RunState()
        scene = Scene(True)
        player = Player(state)
        player.update(0)
        scene.add_entity(player)
        system = BossFightSystem(scene, get_enemy_registry())
        phase = get_phases(state)[4]
        system.load_phase(phase)
        system.intro_remaining = 0
        system._begin_next_wave()
        EventBus.emit(Events.PLAYER_DIED, player)
        self.assertFalse(system.active)
        self.assertFalse(system.pending)
        before = len(scene.entities)
        system.update(100)
        self.assertEqual(len(scene.entities), before)
        scene.clear_scene()
        for entity in phase.default_entities.values():
            entity.destroy()


if __name__ == "__main__":
    unittest.main()
