"""Configurações e builders de ondas; nenhuma função depende da Scene."""
from dataclasses import dataclass
from math import ceil, radians, sin, cos, tau
import random
from typing import Literal

from pygame import Vector2

from enemys.buran_enemy import BuranEnemy
from enemys.attacks import AttractionAttack, RotatingBeamAttack
from enemys.patterns import Charge, Float, FlyBy, LaserSweep, MoveTo, Orbit, PrepareLaser, Pursuit, Wait, Yell, ZigZag
from enemys.patterns.telegraphed_fly_by import TargetedSatelliteFlyBy, TelegraphedFlyBy
from enemys.waves import EnemySpawn, Wave
from game_consts import SFX_PATH


def _positive(name, value):
    if value <= 0: raise ValueError(f"{name} deve ser positivo")


@dataclass(frozen=True)
class OrganizedAttackConfig:
    count: int = 8; groups: int = 1; spacing: float = 170; organize_time: float = .5
    hold: float = .3; warning: float = .5; attack_speed: float = 1900; simultaneous: bool = True
    top_ratio: float = .15; rest: float = .2
    def __post_init__(self):
        _positive("quantidade", self.count); _positive("grupos", self.groups); _positive("espaçamento", self.spacing)
        if self.rest < 0: raise ValueError("O intervalo entre ataques organizados não pode ser negativo")


@dataclass(frozen=True)
class PursuitConfig:
    count: int = 4; charges: int = 3; spawn_interval: float = 4.8; speed: float = 1800
    warning: float = .45; charge_duration: float = .9; reposition_interval: float = .45
    def __post_init__(self): _positive("quantidade", self.count); _positive("investidas", self.charges); _positive("velocidade", self.speed)


@dataclass(frozen=True)
class SideAttackConfig:
    per_side: int = 4; spacing: float = 150; interval: float = 1.25; speed: float = 1900
    warning: float = .45; x_margin: float = 120; top_ratio: float = .16; alternate: bool = True
    def __post_init__(self):
        _positive("quantidade por lado", self.per_side); _positive("espaçamento", self.spacing); _positive("velocidade", self.speed)
        if self.interval < 0 or self.warning < 0: raise ValueError("Intervalos não podem ser negativos")


@dataclass(frozen=True)
class FlyByConfig:
    count: int = 8; speed: float = 2200; interval: float = .3; origins: tuple[str, ...] = ("top", "left", "right")
    margin: float = 150; safe_distance: float = 220; seed: int | None = None
    def __post_init__(self):
        _positive("quantidade", self.count); _positive("velocidade", self.speed)
        if not self.origins or not set(self.origins) <= {"top", "left", "right"}: raise ValueError("Origem de rasante inválida")


@dataclass(frozen=True)
class AlienFlyByConfig:
    count: int = 20
    speed: float = 2600
    gap: float = .2
    warning: float = .75
    margin: float = 180
    vertical_margin: float = 150
    seed: int | None = None
    start_from: Literal["left", "right"] = "left"

    def __post_init__(self):
        _positive("quantidade", self.count)
        _positive("velocidade", self.speed)
        _positive("margem", self.margin)
        if self.gap < 0 or self.warning < 0 or self.vertical_margin < 0:
            raise ValueError("Intervalos e margens não podem ser negativos")
        if self.start_from not in ("left", "right"):
            raise ValueError("O ataque alienígena deve começar pela esquerda ou direita")


@dataclass(frozen=True)
class AsteroidRainConfig:
    """Chuva sequencial que cobre a largura com corredores de dois jogadores."""

    direction: Literal["left", "right"] = "left"
    speed: float = 1450
    interval: float = .16
    interval_jitter: float = .06
    angle: float = 18
    player_width: float = 128 * 1.2
    player_clearance: float = 2.0
    margin: float = 180
    seed: int | None = None

    def __post_init__(self):
        if self.direction not in ("left", "right"):
            raise ValueError("A direção da chuva deve ser 'left' ou 'right'")
        for name, value in (("velocidade", self.speed), ("intervalo", self.interval),
                            ("largura do jogador", self.player_width),
                            ("espaçamento", self.player_clearance)):
            _positive(name, value)
        if self.interval_jitter < 0 or not 0 < self.angle < 80 or self.interval_jitter >= self.interval:
            raise ValueError("Variação do intervalo/ângulo da chuva inválidos")


@dataclass(frozen=True)
class CircularFormationConfig:
    count: int = 20; radius: float = 600; rings: int = 2; angular_speed: float = 100
    clockwise: bool = True; center_speed: float = 190; center_y_ratio: float = .36
    duration: float = 20; holes: int = 2; hole_width: float = 50; margin: float = 20
    def __post_init__(self):
        for name, value in (("quantidade", self.count), ("raio", self.radius), ("anéis", self.rings), ("duração", self.duration)): _positive(name, value)
        if self.holes < 0 or not 0 <= self.hole_width < 360: raise ValueError("Buracos inválidos")


@dataclass(frozen=True)
class ZigZagConfig:
    count: int = 12; group_size: int = 3; group_interval: float = 1.2; vertical_speed: float = 430
    amplitude: float = 150; frequency: float = .65; spacing: float = 230; margin: float = 100
    def __post_init__(self): _positive("quantidade", self.count); _positive("grupo", self.group_size); _positive("velocidade", self.vertical_speed)


@dataclass(frozen=True)
class SatelliteConfig:
    origin: Literal["top", "left", "right", "random"] = "top"
    seed: int | None = None
    angle: float = 35; speed: float = 1800; warning: float = 0.2
    scale: float = 7.0; collider_scale: float = .82; rotation: float = 0
    spin_speed: float = 60; margin: float = 220
    def __post_init__(self):
        if self.origin not in ("top", "left", "right", "random"): raise ValueError("Origem do satélite inválida")
        _positive("velocidade", self.speed); _positive("escala", self.scale); _positive("collider", self.collider_scale)


@dataclass(frozen=True)
class MineFloatConfig:
    count: int = 4; drift: tuple[float, float] = (0, 35); amplitude: tuple[float, float] = (150, 45)
    frequency: tuple[float, float] = (.15, .23); duration: float = 24; minimum_distance: float = 200
    attraction: bool = True; attraction_strength: float = 7000; attraction_minimum_distance: float = 90
    def __post_init__(self):
        _positive("quantidade", self.count); _positive("duração", self.duration)
        _positive("distância", self.minimum_distance); _positive("força de atração", self.attraction_strength)
        _positive("distância mínima da atração", self.attraction_minimum_distance)


@dataclass(frozen=True)
class EvilDronePlacement:
    corner: Literal["top_left", "top_right", "bottom_right", "bottom_left"]
    start_angle: float
    sweep_angle: float
    clockwise: bool


@dataclass(frozen=True)
class EvilDroneWaveConfig:
    placements: tuple[EvilDronePlacement, ...] = (
        EvilDronePlacement("top_left", 0, 90, True),
        EvilDronePlacement("top_right", 180, 90, False),
        EvilDronePlacement("bottom_right", 180, 90, True),
        EvilDronePlacement("bottom_left", 0, 90, False),
    )
    margin: float = 180
    entry_duration: float = 1.0
    preparation_duration: float = .8
    beam_duration: float = 3.5
    exit_duration: float = .8
    spawn_interval: float = 6.4
    beam_width: float = 18

    def __post_init__(self):
        if not self.placements:
            raise ValueError("A onda precisa de pelo menos um drone do mal")
        for name, value in (("margem", self.margin), ("entrada", self.entry_duration),
                            ("preparação", self.preparation_duration),
                            ("raio", self.beam_duration), ("saída", self.exit_duration),
                            ("intervalo", self.spawn_interval), ("largura", self.beam_width)):
            _positive(name, value)
        if any(item.corner not in {"top_left", "top_right", "bottom_right", "bottom_left"}
               or item.sweep_angle < 0 for item in self.placements):
            raise ValueError("Posição ou arco do drone do mal inválido")


def organized_attack(enemy, width, height, config=OrganizedAttackConfig()):
    result = []
    columns = max(1, int(width // config.spacing))
    for i in range(config.count):
        col, row = i % columns, i // columns
        x = width / 2 + (col - (min(columns, config.count) - 1) / 2) * config.spacing
        anchor, start = Vector2(x, height * config.top_ratio + row * config.spacing), Vector2(x, -160 - row * 80)
        group = i % config.groups
        delay = 0 if config.simultaneous else group * (config.warning + .5)
        def movement(start=start, anchor=anchor, delay=delay):
            return [MoveTo(start, anchor, config.organize_time), Wait(anchor, config.hold + delay),
                    Yell(anchor, SFX_PATH + enemy + "_attack.mp3"),
                    Charge(anchor, config.attack_speed, config.warning)]
        result.append(EnemySpawn(enemy, movement, delay=0, group=group))
    return Wave(f"Ataque organizado ({enemy})", tuple(result), rest=config.rest)


def pursuit_wave(enemy, width, height, config=PursuitConfig()):
    spawns = []
    for i in range(config.count):
        x = width * (.25 + .5 * (i % 2)); start = Vector2(x, -150)
        anchor = Vector2(x, height * .16)
        def movement(start=start, anchor=anchor):
            return [MoveTo(start, anchor, .7), Pursuit(anchor, config.charges, config.speed,
                    config.warning, config.charge_duration, config.reposition_interval, anchor,
                    exit_bounds=(0, 0, width, height))]
        spawns.append(EnemySpawn(enemy, movement, delay=i * config.spawn_interval))
    return Wave(f"Perseguição ({enemy})", tuple(spawns))


def side_attack(enemy, width, height, config=SideAttackConfig()):
    ordered = []
    side_rows = ((side, row) for row in range(config.per_side) for side in (0, 1)) if config.alternate else (
        (side, row) for side in (0, 1) for row in range(config.per_side))
    for side, row in side_rows:
            x = config.x_margin if side == 0 else width - config.x_margin
            anchor = Vector2(x, height * config.top_ratio + row * config.spacing)
            start = Vector2(-160 if side == 0 else width + 160, anchor.y)
            ordered.append((side, row, start, anchor))
    spawns = []
    for order, (side, row, start, anchor) in enumerate(ordered):
        movement = lambda s=start, a=anchor: [MoveTo(s, a, .7),
            Yell(a, SFX_PATH + enemy + "_attack.mp3"), Charge(a, config.speed, config.warning)]
        spawns.append(EnemySpawn(enemy, movement, delay=order * config.interval, group=order))
    return Wave(f"Ataque lateral ({enemy})", tuple(spawns))


def safe_flybys(enemy, width, height, player_position=None, config=FlyByConfig()):
    rng, spawns = random.Random(config.seed), []
    player = Vector2(player_position) if player_position is not None else Vector2(width / 2, height * .82)
    # A gaivota, assim como os demais sprites móveis, já aponta para baixo.
    # Portanto, não precisa da meia-volta que invertia sua orientação/eixo.
    facing_offset = 0
    for i in range(config.count):
        origin = config.origins[i % len(config.origins)]
        for _ in range(20):
            if origin == "top":
                x = rng.uniform(config.margin, width - config.margin); start, end = Vector2(x, -config.margin), Vector2(x, height + config.margin)
            else:
                y = rng.uniform(config.margin, height - config.margin); left = origin == "left"
                start, end = Vector2(-config.margin if left else width + config.margin, y), Vector2(width + config.margin if left else -config.margin, y)
            if start.distance_to(player) >= config.safe_distance: break
        spawns.append(EnemySpawn(
            enemy,
            lambda s=start, e=end: [FlyBy(s, e, config.speed, facing_offset)],
            delay=i * config.interval,
        ))
    return Wave(f"Rasgando os céus ({enemy})", tuple(spawns))


def alien_flybys(width, height, config=AlienFlyByConfig(), enemy="alien"):
    """Cria rasantes rápidos, alternados e estritamente sequenciais."""
    if height <= config.vertical_margin * 2:
        raise ValueError("A margem vertical não deixa espaço para o ataque alienígena")

    rng = random.Random(config.seed)
    # O Buran deve começar e terminar com o sprite inteiro fora da tela.
    horizontal_margin = config.margin + (BuranEnemy.SCALE / 2 if enemy == "buran" else 0)
    traversal_time = (width + horizontal_margin * 2) / config.speed
    spawn_interval = config.warning + traversal_time + config.gap
    starts_from_left = config.start_from == "left"
    spawns = []
    for index in range(config.count):
        from_left = starts_from_left if index % 2 == 0 else not starts_from_left
        # Dois rasantes da onda do Buran cobrem a borda inferior, um por lado.
        # A faixa aleatória anterior deixava o jogador parado ali fora de risco.
        if enemy == "buran" and index % 3 == 2:
            y = height - config.vertical_margin / 2
        else:
            y = rng.uniform(config.vertical_margin, height - config.vertical_margin)
        start_x, end_x = (-horizontal_margin, width + horizontal_margin) if from_left else (
            width + horizontal_margin, -horizontal_margin
        )
        start, end = Vector2(start_x, y), Vector2(end_x, y)
        # A rotação permanece zerada. A arte original olha para a esquerda;
        # espelhar quem entra pela esquerda faz todos olharem para onde vão.
        spawns.append(EnemySpawn(
            enemy,
            lambda s=start, e=end: [
                TelegraphedFlyBy(
                    s, e, config.speed, warning=config.warning, initial_rotation=0
                )
            ],
            delay=index * spawn_interval,
            group=index,
            options={"flip_x": from_left},
        ))
    return Wave("Rasantes do Buran" if enemy == "buran" else "Rasantes alienígenas",
                tuple(spawns))


def asteroid_rain(width: float, height: float,
                  config: AsteroidRainConfig = AsteroidRainConfig()) -> Wave:
    """Distribui faixas regulares, mas embaralha a ordem de queda."""
    spacing = config.player_width * config.player_clearance
    vertical_distance = height + config.margin * 2
    angle = radians(config.angle)
    horizontal_shift = vertical_distance * sin(angle) / cos(angle)
    if config.direction == "left":
        first_x, last_x, horizontal_sign = 0.0, width + horizontal_shift, -1
    else:
        first_x, last_x, horizontal_sign = -horizontal_shift, width, 1

    lane_count = ceil((last_x - first_x) / spacing) + 1
    lane_spacing = (last_x - first_x) / max(1, lane_count - 1)
    lanes = list(range(lane_count))
    rng = random.Random(config.seed)
    rng.shuffle(lanes)

    elapsed = 0.0
    spawns = []
    for sequence, lane in enumerate(lanes):
        x = first_x + lane * lane_spacing
        start = Vector2(x, -config.margin)
        direction = Vector2(horizontal_sign * sin(angle), cos(angle))
        end = start + direction * (vertical_distance / direction.y)
        if sequence:
            elapsed += config.interval + rng.uniform(-config.interval_jitter,
                                                       config.interval_jitter)
        movement = lambda s=start, e=end: [FlyBy(s, e, config.speed, facing_offset=180)]
        spawns.append(EnemySpawn(
            "asteroid", movement, delay=elapsed, group=sequence,
            options={"flip_x": config.direction == "right"},
        ))
    return Wave("Chuva de asteroides", tuple(spawns))


def circular_angles(config):
    """Retorna ângulos fora de setores reservados, garantindo buracos reais."""
    if config.count == 0: return []
    holes = [i * 360 / config.holes for i in range(config.holes)] if config.holes else []
    candidates = [i * 360 / max(config.count * 8, 360) for i in range(max(config.count * 8, 360))]
    allowed = [a for a in candidates if all(abs((a-h+180) % 360-180) >= config.hole_width / 2 for h in holes)]
    return [allowed[int(i * len(allowed) / config.count)] for i in range(config.count)]


def circular_formation(enemy, width, height, config=CircularFormationConfig()):
    angles, spawns = circular_angles(config), []
    for i, angle in enumerate(angles):
        ring = i % config.rings; radius = config.radius * (ring + 1) / config.rings
        center = Vector2(width / 2, height * config.center_y_ratio)
        slot = center + Vector2(radius, 0).rotate(angle)
        start = Vector2(slot.x, -config.margin - 100)
        speed = -abs(config.angular_speed) if config.clockwise else abs(config.angular_speed)
        pattern = lambda s=start, target=slot, c=center, r=radius, a=angle: [
            MoveTo(s, target, 1.2),
            Orbit(c, r, a, speed, config.center_speed, config.duration,
                  (config.margin + r, width-config.margin-r)),
        ]
        spawns.append(EnemySpawn(enemy, pattern))
    return Wave(f"Formação circular ({enemy})", tuple(spawns))


def zigzag_wave(enemy, width, height, config=ZigZagConfig()):
    spawns = []
    for i in range(config.count):
        within, group = i % config.group_size, i // config.group_size
        members = min(config.group_size, config.count - group * config.group_size)
        x = width / 2 + (within - (members - 1) / 2) * config.spacing
        start = Vector2(x, -100); duration = (height + 200) / config.vertical_speed
        movement = lambda s=start, phase=within * tau/config.group_size: [ZigZag(s, config.vertical_speed,
            config.amplitude, config.frequency, duration, phase, (config.margin, width-config.margin))]
        spawns.append(EnemySpawn(enemy, movement, delay=group * config.group_interval, group=group))
    return Wave(f"Zigue-zague ({enemy})", tuple(spawns))


def satellite_flyby(width, height, config=SatelliteConfig()):
    rng = random.Random(config.seed)
    origin = rng.choice(("left", "right")) if config.origin == "random" else config.origin
    if origin == "top":
        sign = rng.choice((-1, 1))
        start = Vector2(rng.uniform(config.margin, width - config.margin), -config.margin)
        direction = Vector2(0, 1).rotate(config.angle * sign)
        distance = (height + 2 * config.margin) / abs(direction.y)
    else:
        sign = 1 if origin == "left" else -1
        start = Vector2(-config.margin if sign > 0 else width + config.margin, height * .2)
        direction = Vector2(sign, 0).rotate(config.angle * sign)
        if direction.y < 0:
            direction.y *= -1
        distance = (width + 2 * config.margin) / abs(direction.x)
    end = start + direction.normalize() * distance
    movement = lambda: [TargetedSatelliteFlyBy(start, end, config.speed, config.warning,
                                         config.spin_speed, config.rotation)]
    return Wave("Satélite quebrado", (EnemySpawn("broken_satellite", movement,
                options={"scale": config.scale, "collider_scale": config.collider_scale}),))


def floating_mines(width, height, config=MineFloatConfig()):
    horizontal_spacing = width / (config.count + 1)
    if config.count > 1 and horizontal_spacing < config.minimum_distance:
        raise ValueError("A resolução não comporta a distância mínima entre minas")
    spawns = []
    for i in range(config.count):
        x = horizontal_spacing * (i + 1)
        y = height * (.27 + .08 * (i % 2)); base, start = Vector2(x, y), Vector2(x, -180)
        movement = lambda s=start, b=base, phase=i * tau/max(1, config.count): [MoveTo(s, b, 1.2), Float(b, config.drift, config.amplitude, config.frequency, (phase, phase/2), config.duration)]
        attack = (lambda: AttractionAttack(config.attraction_strength,
                                           config.attraction_minimum_distance)) if config.attraction else (lambda: None)
        spawns.append(EnemySpawn("mine", movement, attack))
    return Wave("Minas flutuantes", tuple(spawns))


def evil_drone_sweeps(width, height, config=EvilDroneWaveConfig()):
    """Agenda um drone por vez; cada posição define sentido e arco próprios."""
    anchors = {
        "top_left": Vector2(config.margin, config.margin),
        "top_right": Vector2(width - config.margin, config.margin),
        "bottom_right": Vector2(width - config.margin, height - config.margin),
        "bottom_left": Vector2(config.margin, height - config.margin),
    }
    outward = {
        "top_left": Vector2(-320, 0),
        "top_right": Vector2(320, 0),
        "bottom_right": Vector2(320, 0),
        "bottom_left": Vector2(-320, 0),
    }
    spawns = []
    for index, placement in enumerate(config.placements):
        anchor = anchors[placement.corner]
        outside = anchor + outward[placement.corner]
        movement = lambda a=anchor, o=outside, p=placement: [
            MoveTo(o, a, config.entry_duration,
                   LaserSweep._sprite_rotation(p.start_angle)),
            PrepareLaser(a, p.start_angle, config.preparation_duration),
            LaserSweep(a, p.start_angle, p.sweep_angle, p.clockwise,
                       config.beam_duration),
            MoveTo(a, o, config.exit_duration,
                   LaserSweep._sprite_rotation(
                       p.start_angle + (p.sweep_angle if p.clockwise else -p.sweep_angle))),
        ]
        attack = lambda: RotatingBeamAttack(width=config.beam_width)
        spawns.append(EnemySpawn("evil_drone", movement, attack,
                                 delay=index * config.spawn_interval, group=index))
    return Wave("Varredura dos drones do mal", tuple(spawns))
