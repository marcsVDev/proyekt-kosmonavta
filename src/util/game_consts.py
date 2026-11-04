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
PLAYER_IMG_PATH = ASSETS_PATH + "player/foguete.png"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080