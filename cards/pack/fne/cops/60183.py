from . import *

# Crooked Cop


def GetAbilities() -> Sequence['Ability']:
    def crooked_cop_defeated(
        effect: 'Effect',
        message: 'Message.WhenUnitBeDefeated',
    ) -> None:
        if message.defeating_player:
            message.defeating_player.DealEncounterCards(1, effect)

    def crooked_cop_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        player = message.GetToPlayer()
        player.GetIdentity().TakeIndirectDamage(effect.this, 2, effect)

    return [
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            crooked_cop_defeated,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            crooked_cop_boost,
        ),
    ]
