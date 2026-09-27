from pygame import Vector2

from entities.enemy import Enemy
from game_consts import ENEMYS_PATH


class RobotSeagullEnemy(Enemy):
    LOOK_AT_PLAYER = False
    FRAME_SIZE = 128
    SCALE = 128
    MIDDLE_SCALE = SCALE / 2
    DEFAULT_SPRITESHEET = ENEMYS_PATH + "gaivotarobo.png"
    DEFAULT_SFX_PATH = None
    DRAW_COLLIDER = False
    _C = Vector2(64, 64)
    MIDDLE_VERTICES = [
        Vector2(7, 55) - _C,
        Vector2(49, 35) - _C,
        Vector2(64, 18) - _C,
        Vector2(79, 35) - _C,
        Vector2(121, 55) - _C,
        Vector2(77, 83) - _C,
        Vector2(64, 112) - _C,
        Vector2(51, 83) - _C,
    ]
