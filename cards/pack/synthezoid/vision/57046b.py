from . import *

def GetAbilities() -> Sequence['Ability']:
    def intangible(effect: 'Effect', message: 'Message.WhenUnitWouldTakeDamage') -> None:
        message.PreventDamage(1, effect)

    return [
        *AbilityFactory.GiveKeywordToAttached(Leader, scheme=1),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            CardFinder(name="Vision", card_type=Leader),
            intangible,
        ),
    ]
