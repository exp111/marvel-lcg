from . import *


def GetAbilities() -> Sequence['Ability']:
    def jonah(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        Unused(message)
        effect.GetInitiator().DrawUp(2, effect)

    ability = AbilityFactory.WhenInYourPlayTurn(AbilityType.Action, jonah)
    for cost in StaminaCost():
        ability.SetCostFunc(cost)
    ability.SetCostFunc(CostFunc.DealPlayerEncounterCard(1, "Initiator"))
    return [ability]
