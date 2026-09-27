"""Catálogo de inimigos e rodadas por ambiente; coordenadas relativas à resolução."""
from functools import partial

from pygame import Vector2

from enemys.attacks import AttractionAttack
from enemys.alien_enemy import AlienEnemy
from enemys.asteroid_enemy import AsteroidEnemy
from enemys.broken_satellite_enemy import BrokenSatelliteEnemy
from enemys.buran_enemy import BuranEnemy
from enemys.behaviors import (
    AlienFlyByConfig, AsteroidRainConfig, CircularFormationConfig, FlyByConfig, MineFloatConfig, OrganizedAttackConfig,
    PursuitConfig, SatelliteConfig, SideAttackConfig, ZigZagConfig,
    alien_flybys, asteroid_rain, circular_formation, evil_drone_sweeps, floating_mines,
    organized_attack, pursuit_wave, safe_flybys, satellite_flyby, side_attack,
    zigzag_wave,
)
from enemys.drone_enemy import DroneEnemy
from enemys.boss_drone_enemy import BossDroneEnemy
from enemys.evil_drone_enemy import EvilDroneEnemy
from enemys.gaivota_enemy import GaivotaEnemy
from enemys.robot_seagull_enemy import RobotSeagullEnemy
from enemys.laser_ship_enemy import LaserShipEnemy
from enemys.mother_ship_enemy import MotherShipEnemy
from enemys.mine_enemy import MineEnemy
from enemys.patterns import Charge, FlyBy, MoveTo, Wait, Yell
from enemys.waves import EnemyRegistry, EnemySpawn, Wave
from game_consts import SCREEN_HEIGHT as H, SCREEN_WIDTH as W, SFX_PATH
from util.resources import load_image, load_sound


def get_enemy_registry():
    registry = EnemyRegistry()
    for name, enemy_type in (("drone", DroneEnemy), ("boss_drone", BossDroneEnemy), ("gaivota", GaivotaEnemy),
                             ("asteroid", AsteroidEnemy), ("mine", MineEnemy),
                             ("broken_satellite", BrokenSatelliteEnemy),
                             ("buran", BuranEnemy),
                             ("evil_drone", EvilDroneEnemy), ("alien", AlienEnemy),
                             ("robot_seagull", RobotSeagullEnemy),
                             ("laser_ship", LaserShipEnemy)):
        # As ondas fornecem seus próprios movimentos; não carregar o TMJ legado.
        registry.register(name, partial(enemy_type, patterns=[]))
        load_image(enemy_type.DEFAULT_SPRITESHEET)
        if enemy_type.DEFAULT_SFX_PATH:
            load_sound(enemy_type.DEFAULT_SFX_PATH)
    # A nave-mãe é criada diretamente pelo BossFightSystem porque não usa a
    # sequência de movimentos de EnemySpawn.
    registry.register("mother_ship", MotherShipEnemy)
    return registry


def formation_path(slot, count, layout, duration, charge_speed=1800):
    column, row = slot % 6, slot // 6
    x = W * (.10 + column * .16)
    y = H * (.16 + row * .16)
    if layout == "v":
        y += abs(column - 2.5) * H * .045
    elif layout == "diagonal":
        y += column * H * .035
    start = Vector2(x, -160 - row * 150)
    anchor = Vector2(x, y)
    side = -1 if slot % 2 else 1
    sweep = Vector2(max(100, min(W - 100, x + side * W * .12)), y + H * .08)
    if layout == "pincer":
        start = Vector2(-160 if column < 3 else W + 160, y)
    elif layout == "cross":
        sweep = Vector2(W - x, y + H * .14)
    elif layout == "dive":
        sweep = Vector2(W - x, H * .62)
    if layout == "charge":
        return [MoveTo(start, anchor, 1.4), Wait(anchor, 1 + slot * .22),
                Charge(anchor, speed=charge_speed)]
    return [MoveTo(start, anchor, 2), Wait(anchor, duration * .3),
            MoveTo(anchor, sweep, duration * .35),
            MoveTo(sweep, anchor, duration * .35),
            MoveTo(anchor, Vector2(x, H + 180), 3)]


def fly_by_path(slot, count, axis, speed=2200):
    lane = slot % max(1, min(count, 10))
    reverse = slot % 2 == 1
    if axis == "horizontal":
        y = H * (.09 + lane * .09)
        start, end = Vector2(-180, y), Vector2(W + 180, y)
    elif axis == "vertical":
        x = W * (.06 + lane * .098)
        start, end = Vector2(x, -180), Vector2(x, H + 180)
    else:
        raise ValueError(f"Eixo de passagem desconhecido: {axis}")
    if reverse:
        start, end = end, start
    return [FlyBy(start, end, speed + (slot % 3) * 140)]


def enemy_path(enemy, slot, count, layout, duration, charge_speed):
    try:
        path = PATH_FACTORIES[layout](slot, count, duration, charge_speed)
    except KeyError as error:
        raise ValueError(f"Layout de onda desconhecido: {layout}") from error
    if enemy in ("drone", "gaivota") and layout not in ("charge", "horizontal", "vertical"):
        # O único ataque desses inimigos é a investida contra o jogador.
        last_position = path[-1].position.copy()
        path[-1] = Charge(last_position, speed=charge_speed)
    if enemy in ATTACK_SFX:
        path = add_attack_yells(path, ATTACK_SFX[enemy])
    return path


def _formation_factory(layout):
    return lambda slot, count, duration, speed: formation_path(
        slot, count, layout, duration, speed
    )


def _fly_by_factory(axis):
    return lambda slot, count, duration, speed: fly_by_path(slot, count, axis, speed)


# Catálogo de estratégias: estender layouts não exige novos condicionais em enemy_path.
PATH_FACTORIES = {
    layout: _formation_factory(layout)
    for layout in ("v", "diagonal", "pincer", "cross", "dive", "charge")
}
PATH_FACTORIES.update({
    axis: _fly_by_factory(axis) for axis in ("horizontal", "vertical")
})

ATTACK_SFX = {
    "drone": SFX_PATH + "drone_attack.mp3",
    "gaivota": SFX_PATH + "gaivota_attack.mp3",
}


def add_attack_yells(patterns, sound_path):
    """Insere um aviso sonoro imediatamente antes de cada investida."""
    result = []
    for pattern in patterns:
        if isinstance(pattern, Charge):
            result.append(Yell(pattern.position, sound_path, pattern.rotation))
        result.append(pattern)
    return result


def make_wave(name, layout, species, count, duration, charge_speed=1800):
    return Wave(name, tuple(
        EnemySpawn(enemy := species[i % len(species)],
                   partial(enemy_path, enemy, i, count, layout, duration, charge_speed),
                   partial(AttractionAttack, 2600) if enemy == "mine" else no_attack)
        for i in range(count)
    ))


def no_attack():
    return None


def launch_waves():
    return ()


def stratosphere_waves():
    return (
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=8, groups=2, simultaneous=True)),
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=8, groups=2, simultaneous=True)),
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=8, groups=8, simultaneous=False)),
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=8, groups=2, simultaneous=True)),
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=22,  groups=5, simultaneous=False)),
       organized_attack("gaivota", W, H, OrganizedAttackConfig(count=22, groups=3, simultaneous=True)),
       side_attack("gaivota", W, H, SideAttackConfig(per_side=6)),
       pursuit_wave("gaivota", W, H, PursuitConfig(count=3, speed=1900)),
       #safe_flybys("gaivota", W, H, config=FlyByConfig(count=10, speed=800, seed=11)),
       asteroid_rain(W, H, AsteroidRainConfig(
           direction="left", speed=1550, interval=.14, interval_jitter=.05, seed=142347,
       )),
       asteroid_rain(W, H, AsteroidRainConfig(
           direction="right", speed=1550, interval=.14, interval_jitter=.05, seed=13127,
       )),
       asteroid_rain(W, H, AsteroidRainConfig(
            direction="right", speed=1550, interval=.14, interval_jitter=.05, seed=324,
        )),
       asteroid_rain(W, H, AsteroidRainConfig(
            direction="left", speed=1550, interval=.14, interval_jitter=.05, seed=42,
        )),
    )


def near_space_waves():
    return (
        organized_attack("drone", W, H, OrganizedAttackConfig(count=9, attack_speed=2100)),
        alien_flybys(W, H, AlienFlyByConfig(count=8, speed=1800, gap=.4, seed=213),
                     enemy="buran"),
        satellite_flyby(W, H, SatelliteConfig(seed=131)),
        satellite_flyby(W, H, SatelliteConfig(seed=332)),
        # circular_formation("drone", W, H, CircularFormationConfig(count=14)),
        satellite_flyby(W, H, SatelliteConfig(seed=232)),
    )


def deep_space_waves():
    return (
        floating_mines(W, H, MineFloatConfig(count=6)),
        floating_mines(W, H, MineFloatConfig(count=8)),
        evil_drone_sweeps(W, H),
        safe_flybys("drone", W, H, config=FlyByConfig(count=9, speed=1000, seed=23)),
        zigzag_wave("drone", W, H, ZigZagConfig()),
        alien_flybys(W, H, AlienFlyByConfig(
            count=20, speed=2600, gap=.2, start_from="left",
        )),
        pursuit_wave("drone", W, H, PursuitConfig(count=4, speed=2500)),
    )


def mars_orbit_waves():
    # A nave-mãe será integrada quando seu inimigo existir.
    return (        
        make_wave("Investida da escolta", "charge", ("drone",), 18, 12, 2500),
        make_wave("Ultimo bloqueio", "horizontal", ("drone",), 18, 20, 2500),
    )

# gaivota flip
