from . import *

# Scythe Strike

def GetAbilities() -> Sequence['Ability']:

    def scythe_strike(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        if not ActivateGrimReaper(effect, player):
            player.GetIdentity().TakeIndirectDamage(this, 2, effect)

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            scythe_strike,
        ),
    ]

