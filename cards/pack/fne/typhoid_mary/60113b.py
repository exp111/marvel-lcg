from . import *


def GetAbilities() -> Sequence['Ability']:
    def flip_back(effect: 'Effect') -> None:
        this = effect.this.CastTo(Attachment)
        if this.card.face != this:
            return
        Players.ForEachPlayer(
            effect,
            lambda player: player.DealEncounterCards(1, effect),
        )
        this.card.Flip(effect)

    return [
        AbilityFactory.EnemyCannotActivate(
            AbilityType.NonKeyword,
            "AttachedEnemy",
        ),
        AbilityFactory.AfterUnitTookDamage(
            AbilityType.ForcedResponse,
            "AttachedEnemy",
            lambda effect, message: flip_back(effect),
        ),
        AbilityFactory.WhenRoundEnd(
            AbilityType.ForcedResponse,
            None,
            lambda effect, message: flip_back(effect),
        ),
    ]
