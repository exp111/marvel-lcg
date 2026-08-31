from core import *


@dataclass
class TriggeredCandidate:
    """One registered effect bound to one condition in a timing window."""

    effect: 'Effect'
    message: 'Message2'
    message_index: int
    asked_player: 'Player|None'
    descriptor: 'EffectDescriptor'
    ability_slot: int = 0

    @property
    def key(self) -> Tuple[int, int]:
        return (self.effect.object_id, self.message.object_id)

    @property
    def choice_id(self) -> str:
        return (
            f"timing-{self.message_index}-"
            f"{self.effect.object_id}-{self.message.object_id}"
        )

    def GetReplayText(self) -> str:
        """Return a stable replay identity that does not require a UI name."""
        ability_type = self.effect.ability.type.name
        try:
            card_replay_text = self.effect.this.GetReplayText()
        except AttributeError:
            paper = getattr(
                self.effect.this,
                "paper",
                getattr(self.effect.this.card, "paper", None),
            )
            card_id = getattr(paper, "card_id", "internal")
            card_replay_text = (
                f"c{self.effect.this.card.object_id} "
                f"{card_id}"
            )
        return (
            f"timing2 t{self.message_index} {self.message.name} "
            f"a{self.ability_slot} {ability_type} "
            f"{card_replay_text}"
        )

    def GetLegacyReplayText(self) -> str|None:
        """Return the pre-v1.3 development identity when representable."""
        try:
            effect_text = self.effect.GetReplayText()
        except (AssertionError, AttributeError):
            return None
        return f"t{self.message_index} {effect_text} @{self.message.name}"

    def GetDisplayName(self) -> str:
        """Return a concise player-facing label for a timing candidate.

        Ordinary effect names are often only an ability type (for example,
        ``Forced_Response``).  They are sufficient when a player clicked the
        source card, but ambiguous in a simultaneous timing chooser.  Prefix
        the printed source card and prefer a card-script name when one exists.
        """
        ability = self.effect.ability
        source = str(
            getattr(self.effect.this, "name", "Internal Effect") or
            "Internal Effect"
        ).strip()
        explicit_name = str(getattr(ability, "name", "") or "").strip()
        rendered_name = str(
            getattr(self.descriptor, "name", "") or ""
        ).replace("_", " ").strip()
        ability_type = str(ability.type.value).strip()

        generic_names = {
            "",
            ability_type.casefold(),
            ability.type.name.replace("_", " ").casefold(),
        }
        if explicit_name:
            action = explicit_name
        elif rendered_name.casefold() not in generic_names:
            action = rendered_name
        else:
            action = ability_type

        def encode(value: str) -> str:
            return "_".join(value.split())

        encoded_source = encode(source)
        encoded_action = encode(action)
        if encoded_action.casefold().startswith(encoded_source.casefold()):
            return encoded_action
        return f"{encoded_source}:_{encoded_action}"

    def GetOriginLabel(self) -> str:
        """Describe the condition's relevant target for duplicate choices."""
        for attribute in (
            "attacked",
            "who_took_damage",
            "target",
            "scheme",
            "trigger",
        ):
            origin = getattr(self.message, attribute, None)
            if origin == None:
                continue
            name = getattr(origin, "name", None)
            if name:
                return str(name).replace(" ", "_")
        return self.message.name

    def GetTriggerLabel(self) -> str:
        """Describe a duplicate trigger without exposing Python class names."""
        origin = self.GetOriginLabel()
        labels = {
            "AfterUnitAttackUnit": "after_attack_on",
            "AfterUnitAttackEnd": "after_attack",
            "AfterUnitUseBasicPower": "after_basic_power_by",
            "AfterUnitTookDamage": "after_damage_to",
            "AfterUnitBeDefeated": "after_defeat_of",
            "AfterUnitDefeatedUnit": "after_defeating",
            "AfterSchemeBeDefeated": "after_scheme_defeated",
            "AfterMainSchemeCompleted": "after_main_scheme_completed",
            "WhenCardEnterPlay": "when_card_enters_play",
            "AfterCardEnterPlay": "after_card_enters_play",
            "WhenCardRevealed": "when_card_revealed",
            "AfterCardRevealed": "after_card_revealed",
        }
        prefix = labels.get(self.message.name)
        if prefix:
            return f"{prefix}_{origin}"

        import re

        readable = re.sub(
            r"(?<!^)(?=[A-Z])",
            "_",
            self.message.name,
        ).lower()
        return f"{readable}_{origin}"

    def GetDiagnosticText(self) -> str:
        paper = getattr(
            self.effect.this,
            "paper",
            getattr(self.effect.this.card, "paper", None),
        )
        return (
            f"card={getattr(paper, 'card_id', 'internal')} "
            f"effect={self.effect.object_id} "
            f"ability={self.effect.ability.type.name} "
            f"message={self.message.name} "
            f"origin={self.GetOriginLabel()} "
            f"replay={self.GetReplayText()}"
        )

    def TryPrepare(self) -> 'Effect|None':
        from game.event.manager import EventManager

        available = EventManager.FilterAvailableEffects(
            self.message,
            [self.effect],
            self.asked_player,
            self.message.world,
            None,
        )
        if available == [self.effect]:
            return self.effect
        return None

    @staticmethod
    def ConvertReplayId(
        replay_text: str,
        candidates: Sequence['TriggeredCandidate'],
    ) -> str|None:
        """Map a recorded trigger-aware identity to this run's choice id."""
        from game.scene.replay import CommandDescriptor
        import re

        for candidate in candidates:
            if candidate.GetReplayText() == replay_text:
                return candidate.choice_id

        v2_match = re.match(
            r"timing2 t(\d+) ([^ ]+) a(\d+) ([^ ]+) c(\d+) (.+)$",
            replay_text,
        )
        if v2_match:
            message_index = int(v2_match.group(1))
            message_name = v2_match.group(2)
            ability_slot = int(v2_match.group(3))
            ability_type = v2_match.group(4)
            card_object_id = int(v2_match.group(5))
            paper_card_id = v2_match.group(6)

            matching = [
                candidate
                for candidate in candidates
                if candidate.message_index == message_index
                and candidate.message.name == message_name
                and candidate.ability_slot == ability_slot
                and candidate.effect.ability.type.name == ability_type
                and candidate.effect.this.paper.card_id == paper_card_id
            ]
            exact_card = [
                candidate
                for candidate in matching
                if candidate.effect.this.card.object_id == card_object_id
            ]
            if len(exact_card) == 1:
                return exact_card[0].choice_id
            if len(matching) == 1:
                return matching[0].choice_id
            return None

        # Backward compatibility with the first pre-v1.3 timing format.
        match = re.match(r"t(\d+) (e\d+ .* c\d+ .*) @([^ ]+)$", replay_text)
        if not match:
            return None
        message_index = int(match.group(1))
        effect_text = match.group(2)
        message_name = match.group(3)

        matching = [
            candidate
            for candidate in candidates
            if candidate.message_index == message_index
            and candidate.message.name == message_name
        ]
        effect_id_match = re.match(r"e(\d+) ", effect_text)
        if effect_id_match:
            recorded_effect_id = int(effect_id_match.group(1))
            exact_effect = [
                candidate
                for candidate in matching
                if candidate.effect.object_id == recorded_effect_id
            ]
            if len(exact_effect) == 1:
                return exact_effect[0].choice_id
        try:
            effect_ids = CommandDescriptor.FindNewEffectIdInternal(
                effect_text,
                [candidate.effect for candidate in matching],
            )
        except (AssertionError, AttributeError):
            return None
        converted = [
            candidate
            for candidate in matching
            if candidate.effect.object_id in effect_ids
        ]
        if len(converted) == 1:
            return converted[0].choice_id
        return None


class TimingOccurrence:
    """Collect simultaneous condition messages from one game occurrence."""

    def __init__(
        self,
        world: 'World',
        *,
        delay_reveal_responses: bool=False,
    ) -> None:
        self.world = world
        self.messages: List['Message2'] = []
        self.delay_reveal_responses = delay_reveal_responses
        self.state: Literal["collecting", "resolving", "aborted", "closed"] = "collecting"

    def Add(self, *messages: 'Message2|None') -> None:
        assert self.state == "collecting", f"Cannot add to {self.state} timing occurrence"
        self.messages.extend(message for message in messages if message != None)

    def Abort(self) -> None:
        self.state = "aborted"
        self.messages.clear()

    def Resolve(self) -> None:
        if self.state != "collecting":
            return
        self.state = "resolving"
        try:
            if not self.messages:
                return
            if bool(self.world.rule.v18_timing):
                self.world.event_manager.BroadcastTimingWindow(self.messages)
            else:
                for message in self.messages:
                    message.Send()
        except Exception as exc:
            from engine.log import Log

            self.state = "aborted"
            info = Log.OnCrash(
                "MESSAGE",
                exc,
                self.messages[0].name if self.messages else "TimingOccurrence",
                None,
            )
            self.world.render.ErrorOccurred(info)
        finally:
            if self.state != "aborted":
                self.state = "closed"
