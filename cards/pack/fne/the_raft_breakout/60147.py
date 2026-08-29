from . import *


def GetAbilities() -> Sequence['Ability']:
    def attacked(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        player = message.GetAgainstPlayer()
        if not player:
            return
        for boost in ActivationBoostCards(message):
            if Treachery.IsType(boost):
                player.DealEncounterCard(boost, effect)

    return [
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            "This",
            attacked,
        ),
    ]
