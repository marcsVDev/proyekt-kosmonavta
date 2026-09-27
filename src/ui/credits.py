"""Rolagem comemorativa da campanha, sem colisões de combate."""

from dataclasses import dataclass
import math

import pygame

from entities.player import Player
from game_consts import SCREEN_HEIGHT, SCREEN_WIDTH
from initializations.misc import get_font


CREAM = (250, 229, 191)
GOLD = (204, 158, 83)
RED = (177, 48, 49)
INK = (0, 0, 0)

# Atribuições fornecidas pela equipe; este é o único cadastro dos autores.
TEAM = (
    ("MARCOS", "DESENVOLVIMENTO", "Transformou a ideia em um jogo, construindo a experiência que nos leva da Terra a Marte."),
    ("GUSTAVO", "ARTE E ILUSTRAÇÕES", "Deu forma ao universo da missão, aos personagens e aos perigos encontrados pelo caminho."),
    ("WESLEY", "ANIMAÇÕES", "Trouxe movimento e vida às naves, aos inimigos e às cenas da jornada."),
    ("MATEUS", "APOIO EMOCIONAL", "Esteve ao lado da equipe, ajudando a manter a missão em curso até o lançamento."),
)

QUOTE_SOURCES = (
    ("Valentina Tereshkova", "ntrs.nasa.gov/citations/20180002182"),
    ("Sally Ride", "science.nasa.gov/people/sally-ride/"),
    ("Christina Koch", "nasa.gov/podcasts/houston-we-have-a-podcast/the-artemis-ii-astronauts-2/"),
    ("Jessica Watkins", "nasa.gov/podcasts/curious-universe/to-the-stars-with-astronaut-jessica-watkins/"),
)


@dataclass(frozen=True)
class Stage:
    name: str
    heading: str
    description: str
    background: str
    sprites: tuple[tuple[str, int, int, float, str], ...]
    quote: str = ""
    author: str = ""
    fact: str = ""


# Sprite: caminho, largura/altura de um quadro, largura exibida, movimento.
STAGES = (
    Stage("01 / KRASNY MIR", "O ESPAÇO TAMBÉM É DELAS",
          "Uma missão alternativa começa na estação Krasny Mir.",
          "assets/scenery/krasny_mir_station.png",
          (),
          "O voo espacial humano não pode avançar sem a participação ativa das mulheres.",
          "VALENTINA TERESHKOVA", "Na história real, foi a primeira mulher no espaço, em 1963."),
    Stage("02 / ESTRATOSFERA", "A CURIOSIDADE DECOLA",
          "A travessia sobe pelas nuvens e encontra os primeiros perigos.",
          "assets/scenery/ceucomnuvens.png",
          (("assets/enemys/gaivota (1).png", 128, 128, 110, "float"),
           ("assets/enemys/meteor_enemy.png", 128, 128, 90, "spin")),
          "Mantenha o interesse pela ciência e vá bem nas aulas de matemática e ciências.",
          "SALLY RIDE", "Na história real, foi a primeira norte-americana no espaço, em 1983, e incentivou meninas nas ciências."),
    Stage("03 / ESPAÇO PRÓXIMO", "NOVOS CAMINHOS",
          "Satélites, drones e a Terra compõem o arquivo desta etapa.",
          "assets/scenery/espaco_proximo.png",
           (("assets/enemys/satelite_quebrado.png", 90, 90, 60, "spin"),
            ("assets/enemys/drone_animation.png", 128, 128, 47, "float"),
            ("assets/enemys/buran.png", 429, 429, 400, "float")),
          "Faça algo que você ama. Faça o que lhe dá medo.",
          "CHRISTINA KOCH", "Na história real, astronauta da NASA e participante de longas missões na Estação Espacial Internacional."),
    Stage("04 / ESPAÇO PROFUNDO", "ALÉM DO CONHECIDO",
          "A nave atravessa minas e máquinas no espaço profundo.",
          "assets/scenery/espaco_proximo.png",
          (("assets/enemys/minaespacial.png", 256, 256, 170, "spin"),
           ("assets/enemys/navedomal-sheet.png", 124, 124, 115, "float"),
           ("assets/enemys/alien_anim_final.png", 128, 128, 90, "float")),
          "Mulheres como Sally Ride e Mae Jemison abriram caminho para mim e para colegas.",
          "JESSICA WATKINS", "Na história real, astronauta da NASA e geóloga; integrou a Expedição 67 da estação espacial."),
    Stage("05 / ÓRBITA DE MARTE", "DESAFIOS EM ÓRBITA",
          "A nave-mãe e suas escoltas marcam o confronto final do jogo.",
          "assets/scenery/espaco_proximo.png",
          (("assets/enemys/navemaeeuabossfinal.png", 480, 270, 550, "float"),
           ("assets/enemys/gaivotarobo_anim (1).png", 128, 128, 65, "float"),
           ("assets/enemys/navezinhabossfinal.png", 128, 128, 60, "float"),
           ("assets/enemys/aeronavedomal.png", 128, 128, 50, "float")),
          fact="Estes adversários pertencem somente à ficção do jogo."),
    Stage("06 / MARTE", "O FUTURO SE ABRE",
          "Na ficção, Valentina chega a Marte. As conquistas reais das homenageadas aconteceram em outras missões.",
          "assets/scenery/MARTE (1).png",
          (),
          fact="Quando ciência e exploração encontram oportunidades, novas gerações podem ir mais longe."),
)


def wrap(font, text, width):
    """Quebra texto pelo tamanho renderizado, inclusive palavras muito longas."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            while font.size(word)[0] > width:
                cut = 1
                while cut < len(word) and font.size(word[:cut + 1])[0] <= width:
                    cut += 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
        lines.append(current)
    return lines


class CreditsShip:
    """Nave visual com os controles e a inércia do jogo, isolada do combate."""

    def __init__(self, size, scale):
        self.width, self.height = size
        self.size = max(1, round(Player.SCALE * scale))
        self.position = pygame.Vector2(self.width / 2, self.height - self.size / 2)
        self.velocity = pygame.Vector2()
        sheet = pygame.image.load(Player.DEFAULT_SPRITESHEET).convert_alpha()
        self.frames = tuple(pygame.transform.smoothscale(
            sheet.subsurface((index * Player.FRAME_SIZE, 0,
                              Player.FRAME_SIZE, Player.FRAME_SIZE)),
            (self.size, self.size)) for index in range(8))
        self.elapsed = 0.0
        self.tilt = 0.0

    def update(self, delta, keys):
        delta = max(0.0, delta)
        self.elapsed += delta
        direction = pygame.Vector2(
            int(bool(keys[pygame.K_d] or keys[pygame.K_RIGHT]))
            - int(bool(keys[pygame.K_a] or keys[pygame.K_LEFT])),
            int(bool(keys[pygame.K_s] or keys[pygame.K_DOWN]))
            - int(bool(keys[pygame.K_w] or keys[pygame.K_UP])),
        )
        if direction.length_squared():
            direction.normalize_ip()
        speed = Player.SPEED * self.width / SCREEN_WIDTH
        acceleration = (Player.ACCELERATION if direction else Player.BRAKE_ACCELERATION) * self.width / SCREEN_WIDTH
        self.velocity = self.velocity.move_towards(direction * speed, acceleration * delta)
        self.position += self.velocity * delta
        half = self.size / 2
        for axis, limit in (("x", self.width), ("y", self.height)):
            value = getattr(self.position, axis)
            clamped = max(half, min(limit - half, value))
            if clamped != value:
                setattr(self.position, axis, clamped)
                setattr(self.velocity, axis, 0)
        target_tilt = -(self.velocity.x / speed) * Player.MAX_TILT
        self.tilt = pygame.math.lerp(self.tilt, target_tilt,
                                     1 - pow(2, -Player.TILT_RESPONSE * delta))

    def image_and_rect(self):
        frame = self.frames[int(self.elapsed / Player.ANIMATION_FRAME_DURATION) % len(self.frames)]
        image = pygame.transform.rotate(frame, self.tilt)
        return image, image.get_rect(center=self.position)

    def draw(self, screen):
        image, rect = self.image_and_rect()
        screen.blit(image, rect)


class Credits:
    SPEED = 60.0
    FAST_MULTIPLIER = 5.0

    def __init__(self, on_finish, size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        self.on_finish = on_finish
        self.width, self.height = size
        self.scale = min(self.width / 1920, self.height / 1080)
        self.time = 0.0
        self.offset = 0.0
        self.card_width = int(self.width * .83)
        self.card_height = int(self.height * .72)
        self.gap = int(self.height * .18)
        self.margin = (self.width - self.card_width) // 2
        self.fonts = {name: get_font(max(16, int(points * self.scale))) for name, points in
                      (("title", 72), ("heading", 54), ("body", 32), ("quote", 39), ("small", 25), ("micro", 21))}
        self.frames = {}
        self.backgrounds = {}
        self._load_assets()
        self.ship = CreditsShip(size, self.scale)
        mars = pygame.image.load("assets/scenery/MARTE (1).png").convert_alpha()
        mars.set_colorkey(mars.get_at((0, 0)))
        mars_width = self.width
        self.mars = pygame.transform.smoothscale(
            mars, (mars_width, round(mars.get_height() * mars_width / mars.get_width())))
        self.mars_rect = self.mars.get_rect(midtop=(self.width // 2, -int(self.height * .33)))
        self.mars_mask = pygame.mask.from_surface(self.mars)
        self.mars_opaque_bottom = max(rect.bottom for rect in self.mars_mask.get_bounding_rects())
        self.finished = False
        self.cards = [self._stage_card(stage, index) for index, stage in enumerate(STAGES)]
        self.cards.append(self._team_card())
        self.cards.append(self._sources_card())
        self.heights = [card.get_height() for card in self.cards]
        self.tops = []
        top = -self.heights[0] + int(self.height * .15)
        for height in self.heights:
            self.tops.append(top)
            top -= height + self.gap
        # O último cartão sai da tela antes de Marte começar a aparecer.
        self.finish_offset = 2 * self.height - self.tops[-1]

    def _load_assets(self):
        for stage in STAGES:
            if stage.background not in self.backgrounds:
                image = pygame.image.load(stage.background).convert_alpha()
                self.backgrounds[stage.background] = image
            for path, fw, fh, displayed, _ in stage.sprites:
                if path in self.frames:
                    continue
                sheet = pygame.image.load(path).convert_alpha()
                frame_count = max(1, sheet.get_width() // fw)
                size = (max(1, int(displayed * self.scale)), max(1, int(displayed * self.scale * fh / fw)))
                self.frames[path] = tuple(pygame.transform.smoothscale(
                    sheet.subsurface((index * fw, 0, fw, fh)), size)
                    for index in range(frame_count))

    @staticmethod
    def _cover(image, size):
        """Preenche a área sem distorcer a proporção do cenário."""
        width, height = size
        factor = max(width / image.get_width(), height / image.get_height())
        scaled = pygame.transform.smoothscale(image, (math.ceil(image.get_width() * factor),
                                                       math.ceil(image.get_height() * factor)))
        rect = pygame.Rect((scaled.get_width() - width) // 2,
                           (scaled.get_height() - height) // 2, width, height)
        return scaled.subsurface(rect)

    def _text(self, surface, text, x, y, width, font_name="body", color=CREAM, spacing=1.12):
        font = self.fonts[font_name]
        line_height = int(font.get_linesize() * spacing)
        for line in wrap(font, text, width):
            if line:
                surface.blit(font.render(line, True, color), (x, y))
            y += line_height
        return y

    def _base(self, height):
        card = pygame.Surface((self.card_width, height), pygame.SRCALPHA)
        card.fill((0, 0, 0, 224))
        return card

    def _stage_card(self, stage, index):
        card = self._base(self.card_height)
        pad = int(64 * self.scale)
        inner = self.card_width - 2 * pad
        self._text(card, f"ARQUIVO DE MISSÃO  /  {stage.name}", pad, int(35 * self.scale), inner, "small",
                   CREAM if index in (0, len(STAGES) - 1) else GOLD)
        heading_font = "heading" if index else "title"
        self._text(card, stage.heading, pad, int(86 * self.scale), inner, heading_font, CREAM)
        image_rect = self.image_rect(index)
        backdrop = self.backgrounds[stage.background]
        scaled = self._cover(backdrop, image_rect.size)
        card.blit(scaled, image_rect)
        text_x = pad if index % 2 else image_rect.right + int(45 * self.scale)
        text_width = image_rect.left - pad - int(45 * self.scale) if index % 2 else self.card_width - pad - text_x
        y = image_rect.top + int(12 * self.scale)
        if stage.quote:
            y = self._text(card, f"“{stage.quote}”", text_x, y, text_width, "quote") + int(10 * self.scale)
            y = self._text(card, stage.author, text_x, y, text_width, "body", GOLD)
            y = self._text(card, "TRADUÇÃO LIVRE  •  PESSOA REAL", text_x, y, text_width, "micro", GOLD) + int(24 * self.scale)
        y = self._text(card, stage.description, text_x, y, text_width, "body") + int(17 * self.scale)
        self._text(card, stage.fact, text_x, y, text_width, "small", GOLD)
        pygame.draw.line(card, GOLD, (pad, self.card_height - int(60 * self.scale)),
                         (self.card_width - pad, self.card_height - int(60 * self.scale)), 2)
        self._text(card, "PROYEKT KOSMONAVTA  /  HISTÓRIA ALTERNATIVA", pad,
                   self.card_height - int(47 * self.scale), inner, "micro", GOLD)
        return card

    def image_rect(self, index):
        pad = int(64 * self.scale)
        width = int(self.card_width * .43)
        height = int(420 * self.scale)
        x = self.card_width - pad - width if index % 2 else pad
        return pygame.Rect(x, int(215 * self.scale), width, height)

    def _team_card(self):
        height = int(940 * self.scale)
        card = self._base(height)
        pad = int(70 * self.scale)
        width = self.card_width - 2 * pad
        self._text(card, "EQUIPE / CRÉDITOS DO JOGO", pad, int(50 * self.scale), width, "heading", CREAM)
        self._text(card, "EQUIPE DA MISSÃO", pad, int(128 * self.scale), width, "small", GOLD)
        y = int(190 * self.scale)
        for name, role, description in TEAM:
            self._text(card, f"{name} — {role}", pad, y, width, "body", CREAM)
            y = self._text(card, description, pad, y + int(46 * self.scale), width, "small", GOLD) + int(28 * self.scale)
        self._text(card, "UMA CONQUISTA FEITA EM EQUIPE.", pad, height - int(95 * self.scale), width, "body", CREAM)
        return card

    def _sources_card(self):
        height = int(635 * self.scale)
        card = self._base(height)
        pad = int(70 * self.scale)
        width = self.card_width - 2 * pad
        self._text(card, "FONTES E RECURSOS", pad, int(45 * self.scale), width, "heading")
        y = self._text(card, "Arte, sprites, animações e áudio: recursos incluídos no projeto.",
                       pad, int(125 * self.scale), width, "small", GOLD) + int(17 * self.scale)
        y = self._text(card, "Fontes: Pixelify Sans — Stefie Justprince; ARCADE CLASSIC — Jakob Fischer (Pizzadude), com uso não comercial indicado no arquivo da fonte.",
                       pad, y, width, "small", GOLD) + int(20 * self.scale)
        self._text(card, "CITAÇÕES — FONTES ORIGINAIS", pad, y, width, "body")
        y += int(55 * self.scale)
        for author, url in QUOTE_SOURCES:
            y = self._text(card, f"{author}: {url}", pad, y, width, "small", GOLD) + int(7 * self.scale)
        self._text(card, "PESSOAS REAIS. MISSÃO A MARTE FICTÍCIA.", pad, height - int(80 * self.scale), width, "body")
        return card

    def update(self, delta, fast=False, keys=None):
        if self.finished:
            return
        was_scrolling = self.offset < self.finish_offset
        self.time += max(0.0, delta)
        self.ship.update(delta, keys if keys is not None else pygame.key.get_pressed())
        self.offset = min(self.finish_offset, self.offset + max(0.0, delta) * self.SPEED
                          * (self.FAST_MULTIPLIER if fast else 1))
        if was_scrolling:
            # A borda acompanha Marte e mantém a nave fora de sua silhueta
            # até o último quadro da rolagem.
            mars_bottom = self._mars_y() + self.mars_opaque_bottom
            safe_y = min(self.height - self.ship.size / 2,
                         max(self.ship.size / 2, mars_bottom + self.ship.size + 16 * self.scale))
            if self.ship.position.y < safe_y:
                self.ship.position.y = safe_y
                self.ship.velocity.y = 0
        else:
            image, rect = self.ship.image_and_rect()
            ship_mask = pygame.mask.from_surface(image)
            if self.mars_mask.overlap(ship_mask, (rect.x - self.mars_rect.x,
                                                  rect.y - self.mars_rect.y)):
                self.finished = True
                self.on_finish()

    def _mars_y(self):
        return self.mars_rect.y + int(self.offset - self.finish_offset)

    def _draw_sprites(self, screen, stage, index, card_y):
        area = self.image_rect(index).move(self.margin, card_y)
        previous_clip = screen.get_clip()
        screen.set_clip(area)
        count = len(stage.sprites)
        # As naves grandes ficam atrás das pequenas, sem nivelar suas escalas.
        order = sorted(range(count), key=lambda number: stage.sprites[number][3], reverse=True)
        for number in order:
            path, _, _, _, motion = stage.sprites[number]
            frames = self.frames[path]
            frame = frames[int(self.time * (7 if len(frames) > 1 else 1) + number) % len(frames)]
            phase = self.time + number * 1.8
            x = area.left + int((number + 1) * area.width / (count + 1)) - frame.get_width() // 2
            y = area.top + int((.3 + .36 * (number % 2)) * area.height) - frame.get_height() // 2
            if frame.get_width() > area.width * .45:
                x = area.centerx - frame.get_width() // 2
                y = area.centery - frame.get_height() // 2
            if motion == "cross":
                x = area.left + int((self.time * 65 * self.scale + number * 130) % (area.width + frame.get_width())) - frame.get_width()
                y += int(math.sin(phase) * 13 * self.scale)
            elif motion == "spin":
                frame = pygame.transform.rotozoom(frame, math.sin(phase * .45) * 12, 1)
                y += int(math.sin(phase * .8) * 17 * self.scale)
            else:
                y += int(math.sin(phase * .9) * 17 * self.scale)
            screen.blit(frame, (x, y))
        screen.set_clip(previous_clip)

    def draw(self, screen):
        screen.fill(INK)
        mars_y = self._mars_y()
        mars_visible = mars_y + self.mars.get_height() > 0
        if mars_visible:
            screen.blit(self.mars, (self.mars_rect.x, mars_y))
        for index, card in enumerate(self.cards):
            y = int(self.tops[index] + self.offset)
            if y >= self.height or y + card.get_height() <= 0:
                continue
            screen.blit(card, (self.margin, y))
            if index < len(STAGES):
                self._draw_sprites(screen, STAGES[index], index, y)
        if self.offset < self.finish_offset and not mars_visible:
            hint = self.fonts["micro"].render(
                "WASD / SETAS  MOVER     •     ESC  MENU     •     ESPAÇO / SHIFT  ACELERAR", True, CREAM)
            screen.blit(hint, (int(24 * self.scale), self.height - hint.get_height() - int(12 * self.scale)))
        self.ship.draw(screen)
