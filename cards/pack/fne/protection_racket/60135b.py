from . import *


def GetAbilities() -> Sequence['Ability']:
    def excess_damage(
        effect: 'Effect',
        message: 'Message.AfterUnitDefeatedUnit',
    ) -> None:
        PlaceThreatHere(effect, message.excess_damage)

    return [
        AbilityFactory.AfterUnitDealExcessDamage(
            AbilityType.ForcedInterrupt,
            Unit2,
            excess_damage,
            to_target=CardFinder(card_type=Ally) | CardFinder(card_type=Minion),
            conditions=[
                lambda effect, message: IsInThisPlayArea(message.target, effect),
                lambda effect, message:
                    Ally.IsType(message.target) or Worlds.IsExpert(effect),
            ],
        ),
        *ProtectionRacketLossAbilities(),
    ]
