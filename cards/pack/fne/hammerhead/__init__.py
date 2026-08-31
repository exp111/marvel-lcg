from cards.pack import *


HAMMERHEAD = CardFinder(name="Hammerhead", card_type=Villain)
MAGGIA_ENEMY = CardFinder(trait="MAGGIA", card_type=Enemy)


def HammerheadVillainAbilities(extra_damage: int) -> List['Ability']:
    def after_damage(effect: 'Effect', message: 'Message.AfterUnitAttackUnit') -> None:
        target = message.attacked
        if target.IsStunned():
            effect.this.DealDamage([target], extra_damage, effect)
        else:
            Faces.GiveStatus([target], "Stunned", effect)

    return [
        AbilityFactory.AfterUnitAttackAndDamageUnit(
            AbilityType.ForcedResponse,
            "This",
            "Character",
            after_damage,
        ).SetName(
            f"Stun the attacked character; if already stunned, deal "
            f"{extra_damage} damage"
        ),
    ]
