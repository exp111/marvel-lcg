from . import *

# * The Owl


def GetAbilities() -> Sequence['Ability']:
    def the_owl_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        message.would_atk_message.GainPiercing(effect)

    return [
        AbilityFactory.UnitAttackGainKeyword(
            "This",
            piercing=True,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            the_owl_boost,
            during_attack=True,
        ),
    ]
