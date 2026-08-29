from . import *

# Contingency Planning


def GetAbilities() -> Sequence['Ability']:

    def can_attach_to_minion_or_side_scheme(effect: 'Effect', face: 'CardFace') -> bool:
        upgrade = face.CastTo(Upgrade)

        def allows_relevant_target(card_type: Any) -> bool:
            if card_type is None:
                return False
            for relevant_type in [Minion, SchemeSide2]:
                try:
                    if issubclass(relevant_type, card_type):
                        return True
                except TypeError:
                    pass
                try:
                    if issubclass(card_type, relevant_type):
                        return True
                except TypeError:
                    pass
            return False

        for ability in upgrade.ability.Find(func_name="Play"):
            for selector in ability.selectors:
                if not selector:
                    continue
                finder = selector.selector_filter.finder
                if finder and allows_relevant_target(finder.card_type):
                    return True
                if selector.target_text in [
                    "Minion",
                    "SchemeSide2",
                    "EncounterSideScheme",
                    "PlayerSideScheme",
                ]:
                    return True
        return False

    def contingency_planning(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        effect.this.CastTo(Upgrade).TuckCardUnderHere(effect.targets, effect)

    return [
        *AbilityFactory.AttachedCardCanPlayLikeInHand(
            CardFinder(card_type=Upgrade),
        ),
        AbilityFactory.CanPlayThisUpgradeCard(),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            contingency_planning,
            conditions=[
                lambda effect, message:
                    effect.this.GetPlacedCardArea().GetSize() == 0,
            ],
        ).SetTarget(
            Upgrade,
            from_where=["YourHandCards"],
            check_fn=can_attach_to_minion_or_side_scheme,
        ),
    ]
