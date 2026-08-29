from . import *


def GetAbilities() -> Sequence['Ability']:
    def fight(effect: 'Effect', player: 'Player') -> None:
        targets = Worlds.GetOnFieldFriendlyCharacters(
            effect,
            CardFinder(card_type=Hero|Ally),
        )
        target = player.AskChooseFace(targets, effect, forced=True)
        if target:
            effect.this.DealDamage([target], 2, effect)

    return PurpleCommandAbility(
        "Exhaust this card and remove 1 command counter → deal 2 damage to a hero or ally",
        fight,
        conditions=[
            lambda effect, message: bool(
                Worlds.GetOnFieldFriendlyCharacters(
                    effect,
                    CardFinder(card_type=Hero|Ally),
                )
            ),
        ],
    )
