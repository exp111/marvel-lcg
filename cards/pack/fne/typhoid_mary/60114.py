from . import *


def GetAbilities() -> Sequence['Ability']:
    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        identity = message.GetToPlayer().GetIdentity()
        identity.TakeIndirectDamage(
            effect.this,
            3,
            effect,
            operation=lambda damage_message:
                Faces.ExhaustAll([damage_message.trigger], effect)
                if damage_message.took_damage > 0 else None,
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(TYPHOID_VILLAIN),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.HeroAction,
        ).SetCost(Cost("BB")).AnyPlayerCanDoThis(),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Typhoid Mary"),
        ),
    ]
