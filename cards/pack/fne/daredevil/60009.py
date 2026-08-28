from . import *


def GetAbilities() -> Sequence['Ability']:

    def deposition(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        ChooseAndPlaySenseUpgrade(
            player,
            effect,
            ignore_resources_cost=True,
        )
        effect.this.CastTo(Event).RemoveThreatFromSchemes(effect.targets, 2, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            deposition,
        ).SetPlay().SetLabel("thwart").SetTarget(Scheme2),
    ]
