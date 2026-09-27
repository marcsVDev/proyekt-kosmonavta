import pygame
from pygame import Vector2

from entities.character import Character
from events.events import Events
from game_consts import PLAYER_IMG_PATH, SCREEN_HEIGHT, SCREEN_WIDTH, SFX_PATH
from events.event_bus import EventBus
from util.run_state import RunState

class Player(Character):
    MULTIPLIER = 1.2
    SCALE = 128 * MULTIPLIER
    MIDDLE_SCALE = SCALE // 2
    INITIAL_POSITION = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - SCALE)

    DEFAULT_SPRITESHEET = PLAYER_IMG_PATH
    FRAME_SIZE = 128

    ANIMATIONS = {
        "default": [0, 1, 2, 3, 4, 5, 6, 7]
    }
    ANIMATION_FRAME_DURATION = 0.10

    DRAW_COLLIDER = False
    MIDDLE_VECTOR = Vector2(MIDDLE_SCALE, MIDDLE_SCALE)
    MIDDLE_VERTICES = [
        Vector2(62, 1) * MULTIPLIER - MIDDLE_VECTOR,     # TL
        Vector2(65, 1) * MULTIPLIER - MIDDLE_VECTOR,     # TR
        Vector2(67, 23) * MULTIPLIER - MIDDLE_VECTOR,    # MR
        Vector2(78, 47) * MULTIPLIER - MIDDLE_VECTOR,    # MMR
        Vector2(78, 69) * MULTIPLIER - MIDDLE_VECTOR,    # BR
        Vector2(85, 106) * MULTIPLIER - MIDDLE_VECTOR,   # BBR
        Vector2(42, 106) * MULTIPLIER - MIDDLE_VECTOR,   # BBL
        Vector2(49, 69) * MULTIPLIER - MIDDLE_VECTOR,    # BL
        Vector2(49, 47) * MULTIPLIER - MIDDLE_VECTOR,    # MML
        Vector2(60, 23) * MULTIPLIER - MIDDLE_VECTOR,    # ML
    ]

    SPEED = 1200
    ACCELERATION = 9000
    BRAKE_ACCELERATION = 3500
    MAX_TILT = 40
    TILT_RESPONSE = 90

    PLAYER_SFX = SFX_PATH + "player.mp3"
    VOLUME = 80

    def __init__(self, run_state: RunState | None = None):
        EventBus.connect(Events.PLAYER_COLLIDE, self.player_collide)
        self.run_state = run_state if run_state is not None else RunState()
        self.health_config = self.run_state.config
        self.velocity = Vector2()
        self._external_acceleration = Vector2()
        self.free_movement = True
        self.god_mode = False
        self._sound_started = False
        self.invulnerable_remaining = 0.0
        self._blink_elapsed = 0.0
        self._death_emitted = False
        self.time_since_damage = float("inf")
        self.sound = pygame.mixer.Sound(self.PLAYER_SFX)
        self.sound.set_volume(self.VOLUME)

        super().__init__()
        self.previous_position = self.position.copy()

    def update(self, delta):
        self.previous_position = self.position.copy()
        self.time_since_damage += max(0.0, delta)
        if self.invulnerable_remaining > 0:
            self.invulnerable_remaining = max(0.0, self.invulnerable_remaining - delta)
            self._blink_elapsed += max(0.0, delta)
            self.visible = int(self._blink_elapsed / self.health_config.blink_interval) % 2 == 0
            if self.invulnerable_remaining == 0:
                self.visible = True
        else:
            self.visible = True
        if self.can_move:
            if not self._sound_started:
                self.sound.play(-1)
                self._sound_started = True
            self.screen_collide()

        super().update(delta)

    def movement(self, delta):
        if not self.free_movement:
            self.velocity.update(0, 0)
            self._external_acceleration.update(0, 0)
            self._rotation = 0
            return
        keys = pygame.key.get_pressed()
        direction = Vector2(0, 0)

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()
            target_velocity = direction * self.SPEED
            acceleration = self.ACCELERATION

            self.sound.set_volume(self.VOLUME + 30)
        else:
            target_velocity = Vector2()
            acceleration = self.BRAKE_ACCELERATION

        if direction == Vector2(0, 0):
            self.sound.set_volume(self.VOLUME - 80)

        self.velocity = self.velocity.move_towards(target_velocity, acceleration * delta)
        self.velocity += self._external_acceleration * delta
        self._external_acceleration.update(0, 0)
        self.position += self.velocity * delta

        target_tilt = -(self.velocity.x / self.SPEED) * self.MAX_TILT
        blend = 1 - pow(2, -self.TILT_RESPONSE * delta)
        self._rotation = pygame.math.lerp(self._rotation, target_tilt, blend)

    def screen_collide(self):
        if self.position.x + self.MIDDLE_SCALE > SCREEN_WIDTH:
            self.position.x = SCREEN_WIDTH - self.MIDDLE_SCALE
            self.velocity.x = min(0, self.velocity.x)
        elif self.position.x - self.MIDDLE_SCALE < 0:
            self.position.x = self.MIDDLE_SCALE
            self.velocity.x = max(0, self.velocity.x)

        if self.position.y + self.MIDDLE_SCALE > SCREEN_HEIGHT:
            self.position.y = SCREEN_HEIGHT - self.MIDDLE_SCALE
            self.velocity.y = min(0, self.velocity.y)
        elif self.position.y - self.MIDDLE_SCALE < 0:
            self.position.y = self.MIDDLE_SCALE
            self.velocity.y = max(0, self.velocity.y)

    def apply_force(self, acceleration):
        """Acumula uma aceleração externa para o próximo passo de movimento."""
        self._external_acceleration += Vector2(acceleration)

    @property
    def is_invulnerable(self):
        return self.invulnerable_remaining > 0

    def take_damage(self, sources) -> bool:
        sources = tuple(sources)
        for source in sources:
            if getattr(source, "consume_on_player_contact", False):
                source.destroy()
        if self.god_mode or self.is_invulnerable or self.run_state.is_game_over:
            return False
        if not self.run_state.damage(1):
            return False

        centers = [Vector2(source.position) for source in sources
                   if hasattr(source, "position")]
        center = sum(centers, Vector2()) / len(centers) if centers else self.position - Vector2(0, 1)
        away = self.position - center
        if away.length_squared() == 0:
            away = Vector2(0, 1)
        self.velocity += away.normalize() * self.health_config.knockback_speed
        if self.velocity.length() > self.SPEED:
            self.velocity.scale_to_length(self.SPEED)

        self.invulnerable_remaining = self.health_config.invulnerability_duration
        self._blink_elapsed = 0.0
        self.time_since_damage = 0.0
        EventBus.emit(Events.PLAYER_DAMAGED, self, self.run_state.health,
                      sources[0] if sources else None)
        if self.run_state.is_game_over and not self._death_emitted:
            self._death_emitted = True
            self.sound.stop()
            EventBus.emit(Events.PLAYER_DIED, self)
            self.destroy()
        return True

    def player_collide(self, player, collisions):
        if player is not self:
            return
        self.take_damage(collisions)

    def game_started(self):
        super().game_started()

    def destroy(self):
        self.sound.stop()
        EventBus.disconnect(Events.PLAYER_COLLIDE, self.player_collide)
        super().destroy()
