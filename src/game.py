import pygame

from initializations.enemy_waves import get_enemy_registry
from system.wave_system import WaveSystem
from system.boss_fight_system import BossFightSystem
from events.events import Events
from game_consts import BACKGROUND_MUSIC_PATH, BOSS_MUSIC_PATH, SCREEN_HEIGHT, SCREEN_WIDTH
from initializations.ui_inits import get_initial_menu_background, get_play_button
from events.event_bus import EventBus
from ui.title import Title
from ui.ui import UI
from util.phase import Phase
from util.progresssion import Progression
from util.scene import Scene
from util.run_state import RunState
from ui.health_bar import HealthBar
from ui.defeat_overlay import DefeatOverlay
from ui.credits import Credits
from entities.enemy import Enemy
from entities.enemy_projectile import EnemyProjectile
from entities.enemy_beam import EnemyBeam

class Game:
    FPS = 60
    FILL_COLOR = (0,0,0) #(0x4d, 0x9b, 0xe6)
    BACKGROUND_MUSIC_VOLUME = 0.35
    PHASE_TRANSITION_DURATION = 1.0

    def __init__(self):
        pygame.init()  
        pygame.display.set_caption("Projeto Cosmonauta")
        pygame.mixer.init()
        self.start_background_music()

        EventBus.connect(Events.PHASE_CHANGED, self.begin_phase_transition)
        EventBus.connect(Events.PLAYER_DIED, self.player_died)
        EventBus.connect(Events.GAME_COMPLETED, self.game_completed)

        # propriedades
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.scenes: dict[str, Scene] = {}
        self.current_scene: str = "menu"
        self.running = True
        self.god_mode = False
        self.campaign_completed = False
        self.run_state = RunState()
        self._pending_phase = None
        self._phase_transition_remaining = 0.0
        self.credits = None
        self.credits_from_game = False

        inital_menu = Scene(game_scene=False) 

        inital_menu.add_ui(get_play_button(self.play))
        inital_menu.add_entity(get_initial_menu_background())
        inital_menu.add_ui(Title())
        self.scenes["menu"] = inital_menu

        game_scene = Scene(game_scene=True)

        progression = Progression(self.run_state)
        
        game_scene.add_system("progression", progression)
        game_scene.add_system("waves", WaveSystem(game_scene, get_enemy_registry()))
        game_scene.add_system("boss", BossFightSystem(game_scene, get_enemy_registry()))
        self.scenes["game"] = game_scene

        # main loop

        self.loop()

        pygame.mixer.music.stop()
        pygame.quit()

    def start_background_music(self):
        """Inicia uma única trilha contínua para menu e campanha."""
        self.play_music(BACKGROUND_MUSIC_PATH)

    def play_music(self, path):
        """Troca a trilha somente quando o contexto musical muda."""
        if getattr(self, "_current_music_path", None) == path:
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self.BACKGROUND_MUSIC_VOLUME)
        pygame.mixer.music.play(-1)
        self._current_music_path = path

    @property
    def phase_transition_active(self):
        return getattr(self, "_pending_phase", None) is not None

    def begin_phase_transition(self, phase: Phase):
        """Mantém a cena pausada e preta antes de carregar a próxima fase."""
        self._pending_phase = phase
        self._phase_transition_remaining = self.PHASE_TRANSITION_DURATION

    def update_phase_transition(self, delta):
        if not self.phase_transition_active:
            return
        self._phase_transition_remaining -= max(0.0, delta)
        if self._phase_transition_remaining > 0:
            return
        phase = self._pending_phase
        self._pending_phase = None
        self._phase_transition_remaining = 0.0
        self.load_phase(phase)

    def loop(self):        
        clock = pygame.time.Clock()
        delta = 0  

        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key, event.mod)

            self.screen.fill(self.FILL_COLOR)
            if self.current_scene == "credits":
                keys = pygame.key.get_pressed()
                self.credits.update(delta, keys[pygame.K_SPACE] or
                                    keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT], keys)
                if self.current_scene == "credits":
                    self.credits.draw(self.screen)
            elif self.current_scene == "game" and self.phase_transition_active:
                self.update_phase_transition(delta)
            else:
                self.scenes[self.current_scene].run(self.screen, delta, events)

            self.fps = clock.get_fps()
            if self.fps < 30:
                print(f"WARNING FPS: {self.fps}")
            
            pygame.display.flip()

            delta = clock.tick(self.FPS) / 1000

    def play(self):
        if self.current_scene != "menu":
            return
        self.run_state.reset()
        self.campaign_completed = False
        EventBus.emit(Events.GAME_STARTED)

        self.load_phase(self.scenes["game"].get_system("progression", Progression).phases[0])
        self.scenes["game"].destroy_entity("play_btn")
        self.change_scene_to("game")

    def handle_keydown(self, key: int, modifiers: int = 0):
        if (key == pygame.K_o
                and modifiers & pygame.KMOD_CTRL
                and modifiers & pygame.KMOD_SHIFT):
            self.toggle_god_mode()
            return
        if self.current_scene == "menu" and key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.play()
        elif (self.current_scene == "menu" and key == pygame.K_c
              and modifiers & pygame.KMOD_CTRL
              and modifiers & pygame.KMOD_SHIFT):
            self.show_credits()
        elif self.current_scene == "credits" and key == pygame.K_ESCAPE:
            self.return_to_menu()
        elif (self.current_scene == "game" and getattr(getattr(self, "run_state", None), "is_game_over", False)
              and key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
            self.restart_campaign()
        elif (self.current_scene == "game" and key == pygame.K_p
              and modifiers & pygame.KMOD_CTRL
              and modifiers & pygame.KMOD_SHIFT):
            if not self.phase_transition_active:
                self.scenes["game"].skip_dialogues()
        elif self.current_scene == "game" and key == pygame.K_ESCAPE:
            self.return_to_menu()

    def toggle_god_mode(self):
        """Alterna invencibilidade e a detecção de colisões do jogador."""
        self.god_mode = not getattr(self, "god_mode", False)
        game_scene = self.scenes.get("game")
        if game_scene is not None and game_scene.player is not None:
            game_scene.player.god_mode = self.god_mode

    def return_to_menu(self):
        """Limpa a partida atual e prepara uma campanha nova para o próximo play."""
        if self.current_scene == "credits" and not self.credits_from_game:
            self.credits = None
            self.change_scene_to("menu")
            return
        if self.current_scene not in ("game", "credits"):
            return
        game_scene = self.scenes["game"]
        game_scene.clear_scene()
        game_scene.get_system("waves", WaveSystem).reset()
        systems = getattr(game_scene, "systems", {})
        boss = systems.get("boss") if isinstance(systems, dict) else None
        if boss is not None:
            boss.reset()
        game_scene.get_system("progression", Progression).reset()
        self.campaign_completed = False
        self._pending_phase = None
        self._phase_transition_remaining = 0.0
        self.credits = None
        self.credits_from_game = False
        self.play_music(BACKGROUND_MUSIC_PATH)
        self.change_scene_to("menu")

    def restart_campaign(self):
        if self.current_scene != "game" or not self.run_state.is_game_over:
            return
        game_scene = self.scenes["game"]
        game_scene.clear_scene()
        game_scene.get_system("waves", WaveSystem).reset()
        game_scene.get_system("boss", BossFightSystem).reset()
        progression = game_scene.get_system("progression", Progression)
        progression.reset()
        self.run_state.reset()
        self.campaign_completed = False
        EventBus.emit(Events.GAME_STARTED)
        self.load_phase(progression.phases[0])

    def player_died(self, player):
        game_scene = self.scenes.get("game")
        if game_scene is None:
            return
        for entity in tuple(game_scene.entities):
            if isinstance(entity, (Enemy, EnemyProjectile, EnemyBeam)) or getattr(
                    entity, "is_guided_missile", False):
                entity.destroy()
        game_scene.add_ui(DefeatOverlay(), "defeat")

    def game_completed(self):
        if self.current_scene != "game" or self.campaign_completed:
            return
        self.campaign_completed = True
        self.show_credits()

    def show_credits(self):
        if self.current_scene not in ("menu", "game"):
            return
        self.credits_from_game = self.current_scene == "game"
        self.credits = Credits(self.return_to_menu, self.screen.get_size())
        self.change_scene_to("credits")

    def load_phase(self, phase: Phase):
        self.play_music(BOSS_MUSIC_PATH if phase.boss_fight else BACKGROUND_MUSIC_PATH)
        game_scene = self.scenes["game"]
        game_scene.clear_scene()
        print(phase.name)
        for key in phase.default_entities.keys():
            match phase.default_entities[key]:
                case UI():
                    game_scene.add_ui(phase.default_entities[key], key)
                case _:
                    game_scene.add_entity(phase.default_entities[key], key)

        if game_scene.player is not None:
            game_scene.player.free_movement = phase.free_movement
            game_scene.player.god_mode = self.god_mode
        if phase.free_movement and game_scene.player is not None:
            game_scene.add_ui(HealthBar(self.run_state), "health")
        waves = game_scene.get_system("waves", WaveSystem)
        boss = game_scene.get_system("boss", BossFightSystem)
        if phase.boss_fight:
            waves.reset()
            boss.load_phase(phase)
        else:
            boss.reset()
            waves.load_phase(phase)

    def change_scene_to(self, name: str):
         self.current_scene = name
         
if __name__ == "__main__":
    GAME = Game()
