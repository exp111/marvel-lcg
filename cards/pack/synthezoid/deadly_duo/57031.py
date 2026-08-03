from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeWouldBeDefeated') -> None:
        Players.ForEachPlayer(effect, lambda player: player.DiscardDeckTopCards(8, effect))
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.ForcedResponse, "This", defeated)]
