from . import *


def GetAbilities() -> Sequence['Ability']:
    def attacked(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        this = effect.this.CastTo(Minion)
        player = message.GetAgainstPlayer()
        Faces.PlaceCountersOn([this], 1, "barrage", effect)
        if player:
            player.GetIdentity().TakeIndirectDamage(
                this,
                this.GetCounters("barrage"),
                effect,
            )

    return [
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            "This",
            attacked,
        ),
    ]
