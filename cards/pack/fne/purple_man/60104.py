from . import *


def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenUnitBeDefeated') -> None:
        player = message.GetKillerPlayer()
        if player:
            effect.this.DealDamage([player.GetIdentity()], 3, effect)

    return [InfluencedMinionDefeated(defeated)]
