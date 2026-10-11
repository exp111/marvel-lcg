"""Read-only artwork dependencies for launch descriptors, saves and puzzles.

This module inspects data, never card abilities or replay commands. It does not
modify the descriptor being checked or add anything to the replay protocol.
"""
from dataclasses import fields, is_dataclass
from copy import deepcopy
import ast
import json
import re
from pathlib import Path


NUMBERED_IMAGE = re.compile(r"(?<![\w])\d{5}[a-z]?(?![\w])")
SET_FIELDS = frozenset({"encounter_set_names", "encounter_sets", "modular_sets", "nemesis_set"})
CARD_FIELDS = frozenset({
    "hero", "identities", "hero_deck", "obligations", "nemesis_set", "player_deck",
    "villain", "schemes", "set_aside", "encounters", "encounter_deck", "encounter_discard_pile",
    "hand_cards", "player_discard_pile", "player_additional_deck", "card_id", "pic_id",
    "puzzle", "puzzle_command", "puzzle_pre_command",
})


def required_images(payload, manifest, *, kind=None):
    from cards.database import CardsDB
    from engine.file import FileManager
    from engine.file.manager import ENCOUNTER_SETS_FOLDERS

    if kind == "new_game":
        from game.scene.loader import SceneLoader
        # Build the same read-only descriptor that the game will use. In
        # particular, selected difficulty sets replace their default variant;
        # unused modular sets must not block an otherwise ready selection.
        payload = SceneLoader.NewFromJson(
            payload.campaign_json, payload.encounter_set_names, payload.hero_json,
            payload.seed, list(payload.rules), dict(payload.campaign_log),
        )
    elif kind == "scene":
        from game.scene.scene import Scene
        if isinstance(payload, Scene) and hasattr(payload.campaign, "modular_sets"):
            # Uploaded saves have not passed through SceneLoader yet. Inspect
            # the migrated copy, including inferred legacy campaign rewards,
            # without changing the uploaded replay or its recorded choices.
            payload = deepcopy(payload)
            payload.UpdateVersion()

    images = set()
    references = set()
    sets = set()
    known_images = set(manifest.get("cards", {})) | set(manifest.get("aliases", {}))
    known_images |= set(manifest.get("generated", {})) | set(manifest.get("bundled", {}))
    papers = CardsDB.papers

    def visit(value, key="", depth=0):
        if depth > 80:
            raise ValueError("Artwork selection nesting is too deep")
        if is_dataclass(value) and not isinstance(value, type):
            for item in fields(value):
                # Scene migration removes obsolete fields such as
                # CampaignDescriptor.modular_sets from the instance.
                if hasattr(value, item.name):
                    visit(getattr(value, item.name), item.name, depth + 1)
        elif isinstance(value, dict):
            for name, child in value.items():
                # Replay inputs may mention dynamically created cards. They
                # are data and are inspected without running their commands.
                visit(child, name, depth + 1)
        elif isinstance(value, (tuple, list, set)):
            for child in value:
                visit(child, key, depth + 1)
        elif isinstance(value, str):
            if key == "id" and value.startswith(("Puzzle.", ":")):
                # Recorded debug commands may create cards absent from the
                # starting decks. Ordinary effect/object IDs are not card IDs.
                images.update(NUMBERED_IMAGE.findall(value))
            if ((key == "id" and value.startswith(("Puzzle.", ":")))
                    or key in {"puzzle", "puzzle_command", "puzzle_pre_command"}):
                try:
                    command = ast.parse(value.removeprefix(":"))
                except (SyntaxError, ValueError):
                    pass
                else:
                    for node in ast.walk(command):
                        if isinstance(node, ast.Constant) and isinstance(node.value, str):
                            visit(node.value, "card_id", depth + 1)
            if value.startswith(("{", "[")):
                try:
                    visit(json.loads(value), key, depth + 1)
                    return
                except (json.JSONDecodeError, RecursionError):
                    pass
            if key in CARD_FIELDS or key in SET_FIELDS or key == "campaign_id":
                references.add(value)
            if key in CARD_FIELDS:
                images.update(NUMBERED_IMAGE.findall(value))
                for token in value.split(","):
                    token = token.strip()
                    if token in known_images or token in papers:
                        images.add(token)
                    elif not NUMBERED_IMAGE.search(token):
                        # Match the game's explicit card-name lookup without
                        # treating a save comment or player name as artwork.
                        named = next((paper.card_id for paper in papers.values()
                                      if getattr(paper, "name", None) == token), None)
                        if named:
                            images.add(named)
            if key in SET_FIELDS and value and not NUMBERED_IMAGE.search(value):
                sets.add(value)

    visit(payload)
    # Restrict named-set reads to the application's existing registered set
    # files. A launch parameter cannot introduce an arbitrary filename here.
    registered_sets = {
        Path(path).stem: path
        for path in reversed(FileManager.ListFiles(*ENCOUNTER_SETS_FOLDERS.value, ext=".json"))
    }
    seen_sets = set()
    while sets - seen_sets:
        for name in list(sets - seen_sets):
            seen_sets.add(name)
            path = registered_sets.get(name)
            if path:
                with open(path, encoding="utf-8-sig") as source:
                    visit(json.load(source))
            else:
                # Unknown sets must not pass an empty dependency check.
                images.add("unresolved-set:" + name)

    dependencies = manifest.get("dependencies", {})
    pending = list(images | references)
    visited = set()
    while pending:
        identifier = pending.pop()
        if identifier in visited:
            continue
        visited.add(identifier)
        extra = set()
        for key in (identifier, "card:" + identifier, "content:" + identifier):
            extra.update(dependencies.get(key, []))
        if identifier in papers:
            paper = papers[identifier]
            image_id = getattr(paper, "pic_id", "")
            if image_id:
                extra.add(image_id)
            extra.update(CardsDB.linked_papers.get(identifier, []))
            target = CardsDB.full_link_cards.get(identifier)
            if target:
                extra.add(target)
            # The database explicitly identifies the faces. This only requires
            # all of them; it never chooses a scan based on a/b suffixes.
            if re.fullmatch(r"\d{5}[a-z]", identifier):
                extra.update(face for face in papers if face[:5] == identifier[:5])
        images.update(extra)
        pending.extend(extra - visited)
    return images
