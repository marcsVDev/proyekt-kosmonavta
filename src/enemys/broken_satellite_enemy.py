from pygame import Vector2

from entities.enemy import Enemy
from game_consts import ENEMYS_PATH


class BrokenSatelliteEnemy(Enemy):
    """Grande obstáculo diagonal; rotação visual é definida pelo padrão."""
    DEFAULT_SPRITESHEET = ENEMYS_PATH + "satelite_quebrado.png"
    FRAME_SIZE = 90
    MULTIPLIER = 18.0
    SCALE = FRAME_SIZE * MULTIPLIER
    MIDDLE_SCALE = SCALE / 2
    SPRITE_VERTICES = (
        (22, 6), (86,10), (83, 50), (22, 88), (0, 65)
    )
    DRAW_COLLIDER = False

    def __init__(self, patterns=None, scale=2.0, collider_scale=1.0):
        if scale <= 0 or collider_scale <= 0:
            raise ValueError("Escalas do satélite devem ser positivas")
        self.SCALE = self.FRAME_SIZE * scale
        half = self.SCALE / 2
        self.MIDDLE_VERTICES = [
            Vector2(-half * .72, -half * .35) * collider_scale,
            Vector2(half * .72, -half * .35) * collider_scale,
            Vector2(half * .72, half * .35) * collider_scale,
            Vector2(-half * .72, half * .35) * collider_scale,
        ]
        super().__init__(patterns)
