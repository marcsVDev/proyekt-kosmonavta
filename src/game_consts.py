
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ASSETS_PATH = resource_path("assets/")
ENEMYS_PATH = ASSETS_PATH + "enemys/"
SCENERY_PATH = ASSETS_PATH + "scenery/"
UI_PATH = ASSETS_PATH + "ui/"
SFX_PATH = ASSETS_PATH + "sfx/"
BACKGROUND_MUSIC_PATH = SFX_PATH + "ambiente.mp3"
BOSS_MUSIC_PATH = SFX_PATH + "musicfinal.mp3"
PATTERNS_PATH = ASSETS_PATH + "patterns/"
PLAYER_IMG_PATH = ASSETS_PATH + "player/foguete-chamas.png"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
