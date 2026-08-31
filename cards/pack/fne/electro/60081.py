from . import *


def GetAbilities() -> Sequence['Ability']:
    def whiplash_attacked(effect: 'Effect', message: 'Message.WhenUnitWouldAttackUnit') -> None:
        charge = GetElectricCharge(effect)
        if not charge or charge.GetCounters('charge') <= 0:
            return
        Faces.RemoveCountersOn([charge], 1, 'charge', effect)
        boost = Worlds.DiscardEncounterTopCard(effect)
        if boost:
            effect.this.DealDamage([message.attacker], boost.printed_boost, effect)

    return [
        AbilityFactory.WhenUnitWouldAttackUnit(
            AbilityType.ForcedInterrupt,
            "Character",
            "This",
            whiplash_attacked,
        ),
    ]
