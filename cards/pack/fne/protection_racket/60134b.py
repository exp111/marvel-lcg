from . import *


def GetAbilities() -> Sequence['Ability']:
    def attacked(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        effect.this.DealDamage([message.attacker], 1, effect)
        PlaceThreatHere(effect, 1)

    standard = AbilityFactory.AfterUnitAttackEnd(
        AbilityType.ForcedResponse,
        Unit2,
        attacked,
        conditions=[
            lambda effect, message: Worlds.IsStandard(effect),
            lambda effect, message: IsInThisPlayArea(message.attacker, effect),
        ],
    ).LimitOncePerPhase()
    expert = AbilityFactory.AfterUnitAttackEnd(
        AbilityType.ForcedResponse,
        Unit2,
        attacked,
        conditions=[
            lambda effect, message: Worlds.IsExpert(effect),
            lambda effect, message: IsInThisPlayArea(message.attacker, effect),
        ],
    )
    return [standard, expert, *ProtectionRacketLossAbilities()]
