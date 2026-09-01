"""Real-card fixtures for the Rules Reference v1.8 timing play lab.

The two Nova/Jarnbjorn checkpoints are recorded through a running game because
their purpose is to stop inside one live response occurrence.  The remaining
labs are deterministic fixture scenes: the normal scene loader creates the
real campaign and hero decks, then the same restricted puzzle setup API used
by the in-game puzzle editor places the cards needed for manual play.

Run ``python v18_timing_harness.py --write --validate`` from the repository
root to rebuild checkpoints 03-16 with fresh serializer checksums.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from engine import Engine  # noqa: F401 - establishes project import order
from cards.database import CardsDB
from engine.lib import Json, Ver
from game.scene import Scene, SceneLoader


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIRECTORY = REPOSITORY_ROOT / "replays" / "v18_timing"
V18_RULES = [
    "fix_attached_health_flip",
    "fix_attached_health_swap",
    "v16_all",
    "v18_timing",
]


class HeadlessStatistics:
    """Minimal statistics sink required by a real ``Game`` instance."""

    def CanRegisterAbility(self) -> bool:
        return True

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: None


@dataclass(frozen=True)
class TimingFixture:
    filename: str
    title: str
    scenario: str
    heroes: tuple[str, ...]
    seed: int
    commands: tuple[str, ...]
    card_ids: tuple[str, ...]


FIXTURES: tuple[TimingFixture, ...] = (
    TimingFixture(
        "03_defensive_conditioning_constants.json",
        "Defensive Conditioning constants",
        "rhino",
        ("doctor_strange",),
        180003,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("56046")',
        ),
        ("56046",),
    ),
    TimingFixture(
        "04_unuscione_forced_order.json",
        "Unuscione forced ordering",
        "rhino",
        ("nova",),
        180004,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateEncounterDeck("32159", "32163")',
        ),
        ("32159", "32163"),
    ),
    TimingFixture(
        "05_cancel_surge_and_incite.json",
        "Cancel Surge and Incite",
        "rhino",
        ("spider_man",),
        180005,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("01004", "01004", "01088", "01088")',
            'Puzzle.CreateEncounterDeck("01191", "04069")',
        ),
        ("01004", "01088", "01191", "04069"),
    ),
    TimingFixture(
        "06_nested_reveal_attack_defense.json",
        "Nested reveal attack and defense",
        "rhino",
        ("spider_man",),
        180006,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("01078", "01088")',
            'Puzzle.CreateEncounterDeck("01186")',
        ),
        ("01078", "01088", "01186"),
    ),
    TimingFixture(
        "07_keyword_priority_lab.json",
        "Keyword priority lab",
        "rhino",
        ("captain_america",),
        180007,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("03009", "33005", "01088")',
            'Puzzle.CreateEncounterDeck("01167", "16183")',
        ),
        ("03009", "33005", "01167", "16183"),
    ),
    TimingFixture(
        "08_status_timing_lab.json",
        "Tough, Piercing, and Vulnerable",
        "rhino",
        ("spider_man",),
        180008,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("04044", "05015", "01088", "01089", "01090")',
            'Puzzle.CreateEncounterDeck("60182", "60182")',
        ),
        ("04044", "05015", "01088", "01089", "01090", "60182"),
    ),
    TimingFixture(
        "09_retaliate_and_ranged.json",
        "Retaliate and Ranged",
        "rhino",
        ("iron_man",),
        180009,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("04020")',
            'Puzzle.CreateEncounterDeck("01172")',
        ),
        ("04020", "01172"),
    ),
    TimingFixture(
        "10_martyr_consequential_damage.json",
        "Martyr consequential damage",
        "rhino",
        ("nova",),
        180010,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("19012")',
            'Puzzle.CreateEncounterDeck("01167")',
        ),
        ("19012", "01167"),
    ),
    TimingFixture(
        "11_thor_overkill_window.json",
        "Thor overkill response window",
        "rhino",
        ("thor",),
        180011,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("06005", "06018", "06019", "01052", "01088", "01089", "01090")',
            'Puzzle.CreateEncounterDeck("01167")',
        ),
        ("06005", "06018", "06019", "01052", "01088", "01089", "01090", "01167"),
    ),
    TimingFixture(
        "12_indirect_divided_damage.json",
        "Indirect and divided damage",
        "rhino",
        ("captain_marvel",),
        180012,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("04020", "19012", "01088", "01088")',
            'Puzzle.CreateEncounterDeck("29040")',
        ),
        ("04020", "19012", "01088", "29040"),
    ),
    TimingFixture(
        "13_thwart_and_scheme_defeat.json",
        "Basic thwart and side-scheme defeat",
        "rhino",
        ("captain_marvel",),
        180013,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("04047")',
            'Puzzle.CreateEncounterDeck("16127")',
        ),
        ("04047", "16127"),
    ),
    TimingFixture(
        "14_recovery_response_window.json",
        "Recovery response window",
        "rhino",
        ("spider_ham",),
        180014,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateHandCards("44008")',
        ),
        ("30001b", "44008"),
    ),
    TimingFixture(
        "15_scheme_lifecycle.json",
        "Scheme lifecycle",
        "risky_business",
        ("captain_marvel",),
        180015,
        (
            'Puzzle.ClearHand()',
            'Puzzle.CreateEncounterDeck("16127", "16178a")',
        ),
        ("16127", "16178a"),
    ),
    TimingFixture(
        "16_multiplayer_priority.json",
        "Multiplayer response priority",
        "rhino",
        ("captain_marvel", "spider_man"),
        180016,
        (
            'Puzzle.ClearHandFor(0)',
            'Puzzle.ClearHandFor(1)',
            'Puzzle.CreateHandCardsFor(0, "04047")',
            'Puzzle.CreateHandCardsFor(1, "04047")',
            'Puzzle.CreateEncounterDeck("16127")',
        ),
        ("04047", "16127"),
    ),
)


def initialize_database() -> None:
    Ver.Initialize()
    CardsDB.Initialize()


def build_fixture_scene(fixture: TimingFixture) -> Scene:
    scene = SceneLoader.NewScene(
        fixture.scenario,
        None,
        list(fixture.heroes),
        fixture.seed,
    )
    scene.rules = list(V18_RULES)
    scene.SetMetadataBool("is_puzzle", True)
    scene.SetMetadataStr("comment", fixture.title)
    scene.puzzle = list(fixture.commands)
    scene.inputs = []
    return scene


def write_fixture(fixture: TimingFixture) -> Path:
    path = OUTPUT_DIRECTORY / fixture.filename
    path.parent.mkdir(parents=True, exist_ok=True)
    Json.Save(build_fixture_scene(fixture), str(path), ignore_check_sum=False)
    return path


def write_nova_checkpoint(*, both_legal: bool) -> Path:
    """Record the Nova/Jarnbjorn checkpoint through the normal controller.

    Runtime effect/card identities and CRCs are produced by the same command
    and choice serialization used by an interactive game.  Nothing in the
    resulting JSON is patched after the scene saves itself.
    """
    from engine.job import JobManager
    from game.game import Game
    from game.scene.replay.operation import CommandDescriptor
    from game.test import Test
    from game.test.headless import HeadlessDeviceManager

    if not hasattr(JobManager, "condition"):
        JobManager.Initialize()

    filename = (
        "02_nova_jarnbjorn_both_legal.json"
        if both_legal
        else "01_nova_jarnbjorn_unlock.json"
    )
    title = (
        "Nova and Jarnbjorn both initially legal"
        if both_legal
        else "Nova unlocks Jarnbjorn"
    )
    commands = [
        'ChangeForm(c1,"Hero")',
        'Play("Supernova Helmet")',
        'Play("Jarnbjorn")',
        'Exhaust("Supernova Helmet")',
        'Faces.DiscardAll(p.hand_cards.Get(), DebugRule(hero))',
    ]
    if both_legal:
        commands.append('Gain("Strength")')

    command_index = 0
    attacked = False

    def choose(prompt):
        nonlocal command_index, attacked
        if prompt.event_name == "WhenPlayerInTurn" and command_index < len(commands):
            Engine.game.controller_manager.console.SetCommand(
                commands[command_index],
                Engine.game.world,
            )
            command_index += 1
            return CommandDescriptor()

        if prompt.event_name == "WhenPlayerInTurn" and not attacked:
            option = next(
                option
                for option in prompt.options
                if option.get("name") == "Attack"
                and option.get("bind_id") == 1
                and option.get("all_legal_targets")
            )
            attacked = True
            return CommandDescriptor(
                str(option.get("choice_id") or option["id"]),
                [str(option["all_legal_targets"][0])],
                [],
            )

        if prompt.event_name == "AfterUnitAttackUnit":
            return None
        return HeadlessDeviceManager._DefaultChoice(prompt)

    scene = SceneLoader.NewScene("rhino", None, ["nova"], 180002 if both_legal else 180001)
    scene.rules = list(V18_RULES)
    scene.SetMetadataStr("comment", title)
    scene.SetMetadataStr("sign", "v18-timing-integration")
    scene.inputs = []

    devices = HeadlessDeviceManager(choice_provider=choose)
    statistics = HeadlessStatistics()
    game = Game(statistics, devices)
    Engine.statistics = statistics
    Engine.game = game

    was_testing = Test.is_in_test
    Test.is_in_test = True
    try:
        game.session.SetScene(scene, "New")
        game.GameSetup()
        game.GameLoop()
    finally:
        Test.is_in_test = was_testing

    if devices.stopped_prompt is None or not attacked:
        raise AssertionError(f"{filename}: did not reach the attack response window")
    expected_steps = 8 if both_legal else 7
    if len(game.controller_manager.replay.history_inputs) != expected_steps:
        raise AssertionError(
            f"{filename}: expected {expected_steps} inputs, got "
            f"{len(game.controller_manager.replay.history_inputs)}"
        )

    path = OUTPUT_DIRECTORY / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if not scene.Save(str(path), game):
        raise AssertionError(f"{filename}: scene serializer refused the save")
    return path


def write_all(fixtures: Sequence[TimingFixture] = FIXTURES) -> list[Path]:
    initialize_database()
    return [
        write_nova_checkpoint(both_legal=False),
        write_nova_checkpoint(both_legal=True),
        *[write_fixture(fixture) for fixture in fixtures],
    ]


def validate_file(path: Path) -> Scene:
    scene, checksum = Json.LoadAsInternal(str(path), Scene, check_sum="Restrict")
    if checksum != "Ok":
        raise AssertionError(f"{path.name}: checksum={checksum}")
    if "v18_timing" not in scene.rules or "no_v18_timing" in scene.rules:
        raise AssertionError(f"{path.name}: v18_timing is not explicitly enabled")
    return scene


def validate_all() -> None:
    initialize_database()
    for number in range(1, 17):
        matches = list(OUTPUT_DIRECTORY.glob(f"{number:02d}_*.json"))
        if len(matches) != 1:
            raise AssertionError(f"checkpoint {number:02d}: found {matches}")
        validate_file(matches[0])


def run_scene_with_devices(scene: Scene, devices, *, load_type: str="New"):
    """Run an in-memory scene through the real game and device workflow."""
    from game.game import Game
    from game.test import Test
    from engine.job import JobManager

    initialize_database()
    if not hasattr(JobManager, "condition"):
        JobManager.Initialize()
    statistics = HeadlessStatistics()
    game = Game(statistics, devices)
    Engine.statistics = statistics
    Engine.game = game

    was_testing = Test.is_in_test
    Test.is_in_test = True
    try:
        game.session.SetScene(scene, load_type)
        game.GameSetup()
        game.GameLoop()
    finally:
        Test.is_in_test = was_testing

    return game


def run_file_with_devices(path: Path, devices):
    """Fast-forward a serialized checkpoint with a headless device manager."""
    scene = validate_file(path)
    # InTesting uses the controller's normal replay conversion while
    # fast-forwarding every recorded operation.  It stops naturally when
    # the serializer has no further choice rather than requiring a UI
    # click for each replay step.
    return run_scene_with_devices(scene, devices, load_type="InTesting")


def run_file_to_prompt(
    path: Path,
    *,
    event_name: str = "WhenPlayerInTurn",
):
    """Run a serialized checkpoint through a real game to a stable prompt.

    The returned game remains available for state assertions.  The headless
    device exits through the normal game-over path after retaining the exact
    UI prompt descriptors.
    """
    from game.test.headless import HeadlessDeviceManager

    devices = HeadlessDeviceManager(
        stop_when=lambda prompt: event_name in prompt.event_name,
    )
    game = run_file_with_devices(path, devices)
    if devices.stopped_prompt is None:
        raise AssertionError(f"{path.name}: did not reach {event_name}")
    return game, devices


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate", action="store_true")
    arguments = parser.parse_args()

    if arguments.write:
        write_all()
    if arguments.validate or not arguments.write:
        validate_all()
