from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Unused(message)
        Players.ForEachPlayer(
            effect,
            lambda player: player.GetIdentity().TakeIndirectDamage(
                effect.this,
                1,
                effect,
            ),
        )
        villain = Worlds.FindVillain(effect)
        if villain:
            effect.this.DealDamage([villain], "2*", effect)

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
