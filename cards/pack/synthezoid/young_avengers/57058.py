from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        resolved = False
        for minion in Worlds.GetOnFieldEnemies(effect, CardFinder(card_type=Minion)):
            resolved = minion.ResolveAbility(player, AbilityType.WhenRevealed, effect) or resolved
        if not resolved:
            ThisCardGainSurge(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
