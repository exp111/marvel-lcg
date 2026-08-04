from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        Players.ForEachPlayer(effect, lambda player: player.DiscardDeckTopCards(8, effect))
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated, "This", defeated)]
