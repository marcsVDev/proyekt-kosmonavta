from pygame import Vector2

from enemys.pattern_deserializer import EnemyPatternDeserializer
from entities.enemy import Enemy
from game_consts import ENEMYS_PATH, PATTERNS_PATH, SFX_PATH

class GaivotaEnemy(Enemy):
    FLIP_X = True
    LOOK_AT_PLAYER = True
    MULTIPLIER = 1.1
    SCALE = 128 * MULTIPLIER
    MIDDLE_SCALE = SCALE // 2

    DEFAULT_SPRITESHEET = ENEMYS_PATH + "gaivota (1).png"
    FRAME_SIZE = 128
    ANIMATIONS = {"default": (0, 1, 2, 3)}
    ANIMATION_FRAME_DURATION = 0.10

    MIDDLE_VECTOR = Vector2(MIDDLE_SCALE, MIDDLE_SCALE)
    DRAW_COLLIDER = False
    MIDDLE_VERTICES = [
        Vector2(66, 36) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(127, 47) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(127, 68) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(63.5, 102) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(0, 67) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(0, 47) * MULTIPLIER - MIDDLE_VECTOR,
        Vector2(61, 36) * MULTIPLIER - MIDDLE_VECTOR,
    ]

    DEFAULT_SFX_PATH = SFX_PATH + "gaivota_default.mp3"

    def __init__(self, patterns=None):
        if patterns is None:
            patterns = EnemyPatternDeserializer().deserialize(PATTERNS_PATH + "gaivota.tmj")
        super().__init__(patterns=patterns)

    def update(self, delta):
        return super().update(delta)
    
