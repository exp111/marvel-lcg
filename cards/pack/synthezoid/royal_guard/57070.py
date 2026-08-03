from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        if player.GetIdentity().HasTrait("HUNTED"):
            effect.this.CastTo(Minion).DoActivate(player, effect)
        else:
            player.DiscardDeckTopCards(2, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
