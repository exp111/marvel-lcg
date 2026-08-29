from . import *


def GetAbilities() -> Sequence['Ability']:
    def reflect_or_recharge(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        this = effect.this.CastTo(Minion)
        if this.GetCounters("spot") > 0:
            Faces.RemoveCountersOn([this], 1, "spot", effect)
            if message.attacker:
                message.ChangeDealtToTarget(message.attacker, effect)
        else:
            Faces.PlaceCountersOn([this], 1, "spot", effect)

    return [
        AbilityFactory.ThisEnterPlayWithCounters(1, "spot"),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "This",
            reflect_or_recharge,
            is_from_attack=True,
        ),
    ]
