from typing import overload

from entities.enemy import Enemy
from entities.enemy_projectile import EnemyProjectile
from entities.enemy_beam import EnemyBeam
from entities.entity import Entity
from entities.player import Player
from events.event_bus import EventBus
from events.events import Events
from system.system import System
from ui.ui import UI
from ui.dialogue_panel import DialoguePanel


class Scene:
    def __init__(self, game_scene: bool):
        self.entities: list[Entity] = []
        self.ui_items: list[UI] = []
        self.systems: dict[str, System] = {}
        self.blackboard: dict[str, Entity] = {}
        self.player: Player | None = None
        self.enemys: list[Enemy] = []
        self.game_scene = game_scene

    @overload
    def add_entity(self, entity: Entity) -> None: ...

    @overload
    def add_entity(self, entity: Entity, blackboard_name: str) -> None: ...

    def add_entity(self, entity: Entity, blackboard_name: str | None = None) -> None:
        self.entities.append(entity)

        if isinstance(entity, Player):
            self.player = entity
        elif isinstance(entity, Enemy):
            self.enemys.append(entity)

        if blackboard_name is not None:
            self.blackboard[blackboard_name] = entity

    def get_entity[T](self, entity_name: str, et: type[T]) -> T:
        return self.blackboard[entity_name] 

    @overload
    def add_ui(self, ui: UI) -> None: ...

    @overload
    def add_ui(self, ui: UI, blackboard_name: str) -> None: ...

    def add_ui(self, ui: UI, blackboard_name: str | None = None) -> None:
        self.ui_items.append(ui)

        if blackboard_name is not None:
            self.blackboard[blackboard_name] = ui

    def add_system(self, sys_name: str, sys: System):
        self.systems[sys_name] = sys

    def get_system[T](self, sys_name: str, sys: type[T]) -> T:
        return self.systems.get(sys_name)

    def run(self, screen, delta, events):
        modal_ui = next((
            item for item in reversed(self.ui_items)
            if getattr(item, "modal", False) and item.visible and not item.to_destroy
        ), None)

        if modal_ui is None:
            for system in self.systems.values():
                system.update(delta)

        for et in tuple(self.entities):
            if et.to_destroy:
                continue
            if modal_ui is not None and isinstance(et, Player):
                continue

            et.update(delta)

        self._remove_destroyed()
        if self.game_scene and modal_ui is None:
            self.resolve_special_collisions()
            self.check_collisions()
        self._remove_destroyed()

        for item in tuple(self.ui_items):
            if item.to_destroy:
                self.ui_items.remove(item)
                continue

            if modal_ui is not None and item is not modal_ui:
                continue

            item.update(delta, events)
            
        for et in self.entities:
            et.draw(screen)        

        for item in self.ui_items:
            item.draw(screen)

    def check_collisions(self):
        if self.player is None or self.player.to_destroy:
            return

        for entity in self.entities:
            if getattr(entity, "is_mother_ship", False) and not entity.to_destroy:
                entity.block_player(self.player)

        colliding_enemys: list[Enemy] = []
        for enemy in self.entities:
            if getattr(enemy, "is_guided_missile", False):
                continue
            if not (isinstance(enemy, (Enemy, EnemyProjectile, EnemyBeam))
                    or getattr(enemy, "damages_player", False)):
                continue
            if not enemy.visible or enemy.to_destroy:
                continue
            if not self.player._collider_vertices or not enemy._collider_vertices:
                continue

            # Triagem barata antes do SAT. Os limites incluem o polígono inteiro.
            if not isinstance(enemy, EnemyBeam):
                distance = self.player.position - enemy.position
                if isinstance(enemy, Enemy):
                    enemy_radius = enemy.SCALE
                elif isinstance(enemy, EnemyProjectile):
                    enemy_radius = enemy.RADIUS
                else:
                    xs = [point.x for point in enemy._collider_vertices]
                    ys = [point.y for point in enemy._collider_vertices]
                    enemy_radius = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
                reach = self.player.SCALE + enemy_radius
                if abs(distance.x) > reach or abs(distance.y) > reach:
                    continue

            if self.player.collide_with(enemy):
                colliding_enemys.append(enemy)

        if len(colliding_enemys) > 0:
            EventBus.emit(Events.PLAYER_COLLIDE, self.player, colliding_enemys)

    def resolve_special_collisions(self):
        for entity in tuple(self.entities):
            if getattr(entity, "is_guided_missile", False) and not entity.to_destroy:
                entity.resolve_collisions(self)

    def _remove_destroyed(self):
        self.entities[:] = [entity for entity in self.entities if not entity.to_destroy]
        self.enemys[:] = [enemy for enemy in self.enemys if not enemy.to_destroy]
        self.blackboard = {key: value for key, value in self.blackboard.items() if not value.to_destroy}
        if self.player is not None and self.player.to_destroy:
            self.player = None

    def skip_dialogues(self):
        for item in tuple(self.ui_items):
            if isinstance(item, DialoguePanel) and not item.to_destroy:
                item.skip_all()

    def clear_scene(self):
        # Permite que cada entidade libere seus recursos (como sons em loop)
        # antes de ser removida da cena.
        for entity in self.entities:
            entity.destroy()

        self.entities.clear()
        self.player = None
        self.enemys.clear()
        self.ui_items.clear()
        self.blackboard.clear()

    def destroy_entity(self, name: str):
        item = self.blackboard.pop(name, None)
        if item is None:
            return

        item.destroy()

        if isinstance(item, UI):
            self.ui_items.remove(item)
        else:
            self.entities.remove(item)

            if item is self.player:
                self.player = None
            if isinstance(item, Enemy):
                self.enemys.remove(item)
