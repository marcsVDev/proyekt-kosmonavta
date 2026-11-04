import json
from functools import lru_cache
from pathlib import Path

from pygame import Surface

from game_consts import resource_path
from ui.dialogue_panel import DialogueEntry
from util.resources import load_image

PROJECT_ROOT = Path(resource_path("."))
DIALOGUES_PATH = Path(resource_path("assets/dialogues/campaign.json"))

@lru_cache(maxsize=1)
def load_dialogue_data() -> dict:
    with DIALOGUES_PATH.open(encoding="utf-8") as dialogue_file:
        data = json.load(dialogue_file)

    if not isinstance(data.get("characters"), dict):
        raise ValueError("O JSON de diálogos precisa declarar 'characters'")
    if not isinstance(data.get("phases"), dict):
        raise ValueError("O JSON de diálogos precisa declarar 'phases'")
    return data


def get_phase_dialogues(phase_id: str | int) -> list[DialogueEntry]:
    data = load_dialogue_data()
    phase_dialogues = data["phases"].get(str(phase_id))
    if not isinstance(phase_dialogues, list) or not phase_dialogues:
        raise ValueError(f"A fase {phase_id!r} não possui diálogos")

    portraits: dict[str, Surface | None] = {}
    entries: list[DialogueEntry] = []
    for item in phase_dialogues:
        character_id = item.get("character")
        character = data["characters"].get(character_id)
        if not isinstance(character, dict):
            raise ValueError(f"Personagem desconhecido no diálogo: {character_id!r}")

        portrait_path = character.get("portrait")
        if character_id not in portraits:
            portraits[character_id] = (
                load_image(str(PROJECT_ROOT / portrait_path))
                if portrait_path
                else None
            )

        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Fala vazia para o personagem {character_id!r}")

        entries.append(DialogueEntry(
            speaker=str(character.get("name", character_id)).upper(),
            text=text,
            portrait=portraits[character_id],
        ))

    return entries
