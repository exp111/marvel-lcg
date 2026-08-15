from . import *

# Stealth Training


def GetAbilities() -> Sequence['Ability']:

    def stealth_training(effect: 'Effect', message: 'Message.AfterUnitDefeatedScheme') -> None:
        Faces.GiveStatus(effect.targets, "Stunned", effect)

    return [
        AbilityFactory.CanPlayThisUpgradeCard("Players"),
        AbilityFactory.AfterUnitDefeatedScheme(
            AbilityType.Response,
            "You",
            SchemeSide2,
            stealth_training,
            conditions=[
                lambda effect, message: message.exact_defeat,
            ],
        ).SetCostFunc(CostFunc.Exhaust("This"))
        .SetTarget(Enemy, canbe_stunned=True),
    ]
