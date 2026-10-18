from . import *


def GetAbilities() -> Sequence['Ability']:
    # Fear No Evil, p. 13: villains are not in any player's play area.
    # Attacking this scheme's owner does not make a villain eligible here.
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
