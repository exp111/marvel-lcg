from . import *


def GetAbilities() -> Sequence['Ability']:
    def prisoner_defeated(
        effect: 'Effect',
        message: 'Message.AfterUnitBeDefeated',
    ) -> None:
        this = effect.this.CastTo(MainScheme)
        this.RemoveThreatFromSchemes(
            [this],
            2 if message.trigger.HasTrait("ELITE") else 1,
            effect,
        )

    return [
        AbilityFactory.AfterUnitBeDefeated(
            AbilityType.WhenDefeated,
            Minion,
            prisoner_defeated,
        ),
    ]
