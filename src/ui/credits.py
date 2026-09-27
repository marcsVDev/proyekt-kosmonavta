"""Rolagem comemorativa da campanha, sem entidades ou colisões de combate."""

from dataclasses import dataclass
import math
import random

import pygame

from game_consts import SCREEN_HEIGHT, SCREEN_WIDTH
from initializations.misc import get_font
from ui.ui import UI


CREAM = (250, 229, 191)
GOLD = (204, 158, 83)
RED = (177, 48, 49)
INK = (15, 17, 24)

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
          (("assets/player/foguete-chamas.png", 128, 128, 150, "cross"),),
          "O voo espacial humano não pode avançar sem a participação ativa das mulheres.",
          "VALENTINA TERESHKOVA", "Na história real, foi a primeira mulher no espaço, em 1963. Não viajou a Marte."),
    Stage("02 / ESTRATOSFERA", "A CURIOSIDADE DECOLA",
          "A travessia sobe pelas nuvens e encontra os primeiros perigos.",
          "assets/scenery/ceucomnuvens.png",
          (("assets/player/foguete-chamas.png", 128, 128, 130, "cross"),
           ("assets/enemys/gaivota (1).png", 128, 128, 110, "float"),
           ("assets/enemys/meteor_enemy.png", 128, 128, 90, "spin")),
          "Mantenha o interesse pela ciência e vá bem nas aulas de matemática e ciências.",
          "SALLY RIDE", "Na história real, foi a primeira norte-americana no espaço, em 1983, e incentivou meninas nas ciências."),
    Stage("03 / ESPAÇO PRÓXIMO", "NOVOS CAMINHOS",
          "Satélites, drones e a Terra compõem o arquivo desta etapa.",
          "assets/scenery/espaco_proximo.png",
          (("assets/scenery/earth.png", 128, 128, 155, "float"),
           ("assets/enemys/satelite_quebrado.png", 90, 90, 105, "spin"),
           ("assets/enemys/drone_animation.png", 128, 128, 110, "float"),
           ("assets/enemys/buran.png", 429, 429, 100, "float")),
          "Faça algo que você ama. Faça o que lhe dá medo.",
          "CHRISTINA KOCH", "Na história real, astronauta da NASA e participante de longas missões na Estação Espacial Internacional."),
    Stage("04 / ESPAÇO PROFUNDO", "ALÉM DO CONHECIDO",
          "A nave atravessa minas e máquinas no espaço profundo.",
          "assets/scenery/espaco_proximo.png",
          (("assets/player/foguete-chamas.png", 128, 128, 130, "cross"),
           ("assets/enemys/minaespacial.png", 256, 256, 105, "spin"),
           ("assets/enemys/navedomal-sheet.png", 124, 124, 115, "float"),
           ("assets/enemys/alien_anim_final.png", 128, 128, 90, "float")),
          "Mulheres como Sally Ride e Mae Jemison abriram caminho para mim e para colegas.",
          "JESSICA WATKINS", "Na história real, astronauta da NASA e geóloga; integrou a Expedição 67 da estação espacial."),
    Stage("05 / ÓRBITA DE MARTE", "DESAFIOS EM ÓRBITA",
          "A nave-mãe e suas escoltas marcam o confronto final do jogo.",
          "assets/scenery/espaco_proximo.png",
          (("assets/enemys/navemaeeuabossfinal.png", 480, 270, 250, "float"),
           ("assets/enemys/gaivotarobo_anim (1).png", 128, 128, 105, "float"),
           ("assets/enemys/navezinhabossfinal.png", 128, 128, 100, "float"),
           ("assets/enemys/aeronavedomal.png", 128, 128, 85, "float")),
          fact="Estes adversários pertencem somente à ficção do jogo."),
    Stage("06 / MARTE", "O FUTURO SE ABRE",
          "Na ficção, Valentina chega a Marte. As conquistas reais das homenageadas aconteceram em outras missões.",
          "assets/scenery/MARTE (1).png",
          (("assets/player/foguete-chamas.png", 128, 128, 140, "cross"),),
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


class Credits:
    SPEED = 105.0
    FAST_MULTIPLIER = 4.0

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
        self.cards = [self._stage_card(stage, index) for index, stage in enumerate(STAGES)]
        self.cards.append(self._team_card())
        self.cards.append(self._sources_card())
        self.heights = [card.get_height() for card in self.cards]
        self.tops = []
        top = -self.heights[0] + int(self.height * .15)
        for height in self.heights:
            self.tops.append(top)
            top -= height + self.gap
        self.finish_offset = self.height - self.tops[-1]
        rng = random.Random(1963)
        self.stars = [(rng.randrange(self.width), rng.randrange(self.height), rng.choice((1, 1, 2))) for _ in range(100)]

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
        card.fill((20, 22, 30, 248))
        pygame.draw.rect(card, GOLD, card.get_rect(), max(2, int(3 * self.scale)))
        pygame.draw.rect(card, RED, (0, 0, int(17 * self.scale), height))
        return card

    def _stage_card(self, stage, index):
        card = self._base(self.card_height)
        if index in (0, len(STAGES) - 1):
            pygame.draw.rect(card, RED, (int(17 * self.scale), int(3 * self.scale),
                                         self.card_width - int(20 * self.scale), int(193 * self.scale)))
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
        shade = pygame.Surface(image_rect.size, pygame.SRCALPHA)
        shade.fill((10, 13, 22, 75))
        grid_step = max(24, int(48 * self.scale))
        for x in range(0, image_rect.width, grid_step):
            pygame.draw.line(shade, (212, 170, 92, 32), (x, 0), (x, image_rect.height))
        for y in range(0, image_rect.height, grid_step):
            pygame.draw.line(shade, (212, 170, 92, 32), (0, y), (image_rect.width, y))
        card.blit(shade, image_rect)
        pygame.draw.rect(card, GOLD, image_rect, max(2, int(2 * self.scale)))
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

    def update(self, delta, fast=False):
        self.time += max(0.0, delta)
        self.offset += max(0.0, delta) * self.SPEED * (self.FAST_MULTIPLIER if fast else 1)
        if self.offset >= self.finish_offset:
            self.on_finish()

    def _draw_sprites(self, screen, stage, index, card_y):
        area = self.image_rect(index).move(self.margin, card_y)
        previous_clip = screen.get_clip()
        screen.set_clip(area)
        count = len(stage.sprites)
        for number, (path, _, _, _, motion) in enumerate(stage.sprites):
            frames = self.frames[path]
            frame = frames[int(self.time * (7 if len(frames) > 1 else 1) + number) % len(frames)]
            phase = self.time + number * 1.8
            x = area.left + int((number + 1) * area.width / (count + 1)) - frame.get_width() // 2
            y = area.top + int((.3 + .36 * (number % 2)) * area.height) - frame.get_height() // 2
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
        for x, y, radius in self.stars:
            pygame.draw.circle(screen, GOLD, (x, int((y + self.offset * .13) % self.height)), radius)
        pygame.draw.circle(screen, (89, 39, 42), (self.width // 2, self.height // 2), int(self.height * .37), 2)
        pygame.draw.circle(screen, (64, 50, 48), (self.width // 2, self.height // 2), int(self.height * .47), 1)
        for index, card in enumerate(self.cards):
            y = int(self.tops[index] + self.offset)
            if y >= self.height or y + card.get_height() <= 0:
                continue
            screen.blit(card, (self.margin, y))
            if index < len(STAGES):
                self._draw_sprites(screen, STAGES[index], index, y)
        strip = pygame.Surface((self.width, int(46 * self.scale)), pygame.SRCALPHA)
        strip.fill((10, 12, 18, 230))
        screen.blit(strip, (0, self.height - strip.get_height()))
        hint = self.fonts["micro"].render("ESC  MENU     •     SEGURE ESPAÇO OU SHIFT PARA ACELERAR", True, CREAM)
        screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - strip.get_height() // 2)))


class CreditsMenuButton(UI):
    """Entrada textual para os créditos no menu existente."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.font = get_font(42)
        self.label = self.font.render("CRÉDITOS", True, CREAM)
        self.area = self.label.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * .78)))
        self.area.inflate_ip(80, 35)

    def update(self, delta, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.area.collidepoint(event.pos):
                self.callback()

    def draw(self, screen):
        hovered = self.area.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (30, 22, 29), self.area)
        pygame.draw.rect(screen, CREAM if hovered else GOLD, self.area, 3)
        screen.blit(self.label, self.label.get_rect(center=self.area.center))
