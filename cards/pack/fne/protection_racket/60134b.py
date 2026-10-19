from . import *


def GetAbilities() -> Sequence['Ability']:
    # The printed trigger is "is attacked": check the target's play area,
    # then damage the attacker (which can be the shared villain).
    def attacked(effect: 'Effect', message: 'Message.AfterUnitAttackUnit') -> None:
        effect.this.DealDamage([message.attacker], 1, effect)
        PlaceThreatHere(effect, 1)

    standard = AbilityFactory.AfterUnitBeAttacked(
        AbilityType.ForcedResponse,
        Unit2,
        attacked,
        conditions=[
            lambda effect, message: Worlds.IsStandard(effect),
            lambda effect, message: IsInThisPlayArea(message.attacked, effect),
        ],
    ).LimitOncePerPhase()
    expert = AbilityFactory.AfterUnitBeAttacked(
        AbilityType.ForcedResponse,
        Unit2,
        attacked,
        conditions=[
            lambda effect, message: Worlds.IsExpert(effect),
            lambda effect, message: IsInThisPlayArea(message.attacked, effect),
        ],
    )
    return [standard, expert, *ProtectionRacketLossAbilities()]
