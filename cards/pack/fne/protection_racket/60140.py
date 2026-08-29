from . import *


def PlaceAttackExcess(
    effect: 'Effect',
    player: 'Player|None',
    attacks: Sequence['Message.AfterUnitAttackUnit|Message.AttackEndsBeforeDamageDealt'],
) -> None:
    if not player:
        return
    excess = sum(max(0, getattr(attack, "excess_damage", 0)) for attack in attacks)
    scheme = GetProtectionRacketScheme(player, effect)
    if scheme and excess:
        scheme.PlaceThreatOnSchemes([scheme], excess, effect)


def GetAbilities() -> Sequence['Ability']:
    def attacked(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        PlaceAttackExcess(
            effect,
            message.GetAgainstPlayer(),
            message.atk_messages,
        )

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        if not hasattr(message, "would_atk_message"):
            return
        would_attack = message.would_atk_message
        effect.this.effect.RegisterTemp(
            AbilityFactory.AfterUnitAttackEnd(
                AbilityType.Temp2,
                None,
                lambda temp_effect, attack_end: PlaceAttackExcess(
                    effect,
                    message.GetToPlayer(),
                    attack_end.atk_messages,
                ),
                would_atk_message=would_attack,
            ),
            unregister_after_exec=True,
        )

    return [
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            "This",
            attacked,
        ),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
