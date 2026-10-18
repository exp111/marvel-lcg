from . import *


def GetAbilities() -> Sequence['Ability']:
    def excess_damage(
        effect: 'Effect',
        message: 'Message.WhenCalcDealExcessDamage',
    ) -> None:
        PlaceThreatHere(effect, message.excess_damage)

    return [
        # Interrupt the excess damage while the recipient is still in its
        # play area. An after-defeat check loses that location, and damage
        # from a non-character source also qualifies for the printed effect.
        AbilityFactory.WhenUnitAttackDealExcessDamage(
            AbilityType.ForcedInterrupt,
            None,
            excess_damage,
            conditions=[
                lambda effect, message: message.excess_damage > 0,
                lambda effect, message: IsInThisPlayArea(message.target, effect),
                lambda effect, message:
                    Ally.IsType(message.target) or
                    (Worlds.IsExpert(effect) and Minion.IsType(message.target)),
            ],
        ),
        *ProtectionRacketLossAbilities(),
    ]
