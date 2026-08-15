from . import *

# * Cloak


def GetAbilities() -> Sequence['Ability']:

    def cloak(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        Find.FindAndPutIntoPlay(
            effect,
            effect.GetInitiator(),
            name="Dagger",
            card_type=Ally,
        )

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            cloak,
        ).SetCost(Cost("YY"))
        .SetCostFunc(CostFunc.Exhaust("This")),
    ]
