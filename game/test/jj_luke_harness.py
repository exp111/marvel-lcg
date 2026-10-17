"""Regression fixtures for the normally registered Jessica Jones / Luke Cage packs."""

import json
from pathlib import Path

from engine import Engine  # establishes the project's import order
from game.scene import SceneLoader

DATA = Path(__file__).resolve().parents[2] / "data/experimental/jj_luke"


def load_pack_reference():
    """Read the reviewed snapshot without replacing the normal card database."""
    return json.loads((DATA / "cards.json").read_text(encoding="utf-8"))


def build_scene(pack, *, seed=610620):
    hero = {"jj": "jessica_jones", "luke_cage": "luke_cage"}[pack]
    scene = SceneLoader.NewScene("rhino", None, [hero], seed)
    scene.rules = ["v16_all", "v18_timing", "fix_attached_health_flip"]
    scene.campaign.expert = False
    return scene
