"""Deterministic UI choices against the real game controller, without a browser."""
from types import SimpleNamespace

from engine import Engine
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.jj_luke_harness import build_scene
from unit_test import test_jj_luke_first_pass as fixtures


class Gameplay:
    @classmethod
    def setUpClass(cls):
        fixtures.TestFirstPassPacks.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        fixtures.TestFirstPassPacks.tearDownClass.__func__(cls)

    run_commands = fixtures.TestFirstPassPacks.run_commands

    @staticmethod
    def two_players(scene):
        scene.players.append(build_scene("luke_cage" if "61001a" in scene.players[0].hero[0] else "jj").players[0])

    @staticmethod
    def card_id(option):
        return Engine.game.world.object_manager.card_dict[option["bind_id"]].face.paper.card_id

    def descriptor(self, option, target=None):
        choice = HeadlessDeviceManager._DefaultChoice(SimpleNamespace(options=[option]))
        if target:
            ids = [str(t.get("id", t) if isinstance(t, dict) else t)
                   for t in option.get("all_legal_targets", [])]
            selected = [t for t in ids if Engine.game.world.object_manager.card_dict[int(t)].face.paper.card_id == target]
            self.assertTrue(selected, (target, option))
            choice.targets = selected[:1]
        payments = option.get("target_payment", {})
        if payments:
            payment = payments.get(choice.targets[0] if choice.targets else "0", next(iter(payments.values())))
            if payment["payment"]:
                # The renderer lists available resource generators, not complete
                # payments. Fixtures supply the intended resource cards explicitly.
                choice.resources = [str(next(iter(generator))) for generator in payment["payment"]]
        return choice

    def use(self, cid, name=None, target=None):
        def choose(prompt):
            options = [o for o in prompt.options if self.card_id(o) == cid and
                       (name is None or o["name"] == name)]
            self.assertTrue(options, (cid, name, prompt))
            return self.descriptor(options[0], target)
        return choose

    def choices(self, *, responses=(), names=(), target=None, pay_like_turn=False):
        """Accept only requested response cards; never blindly accept mulligans."""
        def choose(prompt):
            if prompt.event_name == "WhenPlayerLikeInTurn" and pay_like_turn:
                return self.descriptor(prompt.options[0])
            for option in prompt.options:
                if any(name in option["name"].replace("_", " ") for name in names):
                    return self.descriptor(option, target)
                if (prompt.event_name != "WhenPlayerChooseAbility"
                        and option["name"] not in ("Defense", "Attack", "Thwart", "Recover", "Play", "Change_Form")
                        and self.card_id(option) in responses):
                    return self.descriptor(option, target)
            for option in prompt.options:
                if option["name"] == "Cancel":
                    return self.descriptor(option)
            return NotImplemented
        return choose

    def observe(self, world, player, prompt):
        def ids(deck):
            return [f.paper.card_id for f in deck.Get()]
        def info(face):
            return dict(id=face.card.object_id, cid=face.paper.card_id,
                        hp=getattr(face, "health", None), atk=getattr(face, "attack", None),
                        max_hp=getattr(face, "max_health", None),
                        thw=getattr(face, "thwart", None), sch=getattr(face, "scheme", None),
                        defense=getattr(face, "defense", None), threat=getattr(face, "threat", None),
                        tough=getattr(face, "tough", None), exhausted=face.IsExhaust(),
                        evidence=face.GetCounters("evidence"), pheromone=face.GetCounters("pheromone"),
                        limb=face.GetCounters("limb"), squirrel=face.GetCounters("squirrel"),
                        block=face.GetCounters("block"), rage=face.GetCounters("rage"),
                        traits=sorted(face.traits),
                        stunned=getattr(face,"stunned",0), confused=getattr(face,"confused",0))
        return {
            "round": world.round_id,
            "hand": ids(player.hand_cards), "deck": ids(player.player_deck),
            "discard": ids(player.discard_pile), "stunned": player.GetIdentity().IsStunned(),
            "confused": player.GetIdentity().IsConfused(),
            "field": [info(c.face) for c in world.object_manager.card_dict.values() if c.face.IsInPlay()],
            "players": [dict(face=p.GetIdentity().paper.card_id, hp=p.GetIdentity().health,
                             tough=p.GetIdentity().tough, hand=ids(p.hand_cards),
                             minions=[m.paper.card_id for m in p.GetEngagedMinions()],
                             encounters=ids(p.dealt_encounter_cards)) for p in world.const_players],
            "actions": [(self.card_id(o), o["name"]) for o in prompt.options],
            "costs": {self.card_id(o): [p["cost"] for p in o.get("target_payment", {}).values()]
                      for o in prompt.options if o["name"] == "Play"},
        }

    def play(self, commands, **kwargs):
        return self.run_commands(self.pack, commands, extra_snapshot=self.observe, **kwargs)

    @staticmethod
    def face(snapshot, cid):
        return next(f for f in snapshot["field"] if f["cid"] == cid)

    @staticmethod
    def hand(*ids):
        return ['puzzle.ClearHand()', 'puzzle.CreateHandCards(' + ','.join(repr(cid) for cid in ids) + ')']

    @staticmethod
    def tough(count):
        return ['hero.GainStatus("Tough",DebugRule(hero))'] * count
