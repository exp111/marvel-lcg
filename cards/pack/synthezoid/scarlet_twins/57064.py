from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeWouldBeDefeated') -> None:
        message.GetToPlayer().DiscardHandCards((1, 1), effect)
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.ForcedResponse, "This", defeated)]
