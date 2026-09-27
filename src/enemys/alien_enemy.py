import pygame
from pygame import Vector2

from entities.enemy import Enemy
from game_consts import ENEMYS_PATH


class AlienEnemy(Enemy):
    """Piloto alienígena que atravessa a tela em rasantes horizontais."""

    LOOK_AT_PLAYER = False
    DEFAULT_SPRITESHEET = ENEMYS_PATH + "alien_anim_final.png"
    DEFAULT_SFX_PATH = None
    MULTIPLY = 1.2
    FRAME_SIZE = 128
    ANIMATIONS = {"default": tuple(range(10))}
    ANIMATION_FRAME_DURATION = 0.10
    SCALE = 128 * MULTIPLY
    DRAW_COLLIDER = False
    DRAW_DANGER_LINE = False

    _SPRITE_CENTER = Vector2(FRAME_SIZE / 2)
    _SPRITE_SCALE = SCALE / FRAME_SIZE
    # Aproximação convexa da silhueta completa (nave e piloto).
    MIDDLE_VERTICES = [
        (Vector2(83, 17) - _SPRITE_CENTER) * _SPRITE_SCALE,
        (Vector2(121, 17) - _SPRITE_CENTER) * _SPRITE_SCALE,
        (Vector2(125, 100) - _SPRITE_CENTER) * _SPRITE_SCALE,
        (Vector2(0, 74) - _SPRITE_CENTER) * _SPRITE_SCALE,
    ]

    def __init__(self, patterns=None, flip_x: bool = False):
        self.flip_x = flip_x
        super().__init__(patterns)

    def scale(self, by):
        super().scale(by)
        if self.flip_x:
            self._image = pygame.transform.flip(self._image, True, False)
