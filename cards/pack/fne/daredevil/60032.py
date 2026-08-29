from . import *


def GetAbilities() -> Sequence['Ability']:

    def sensory_overload(effect: 'Effect', message: 'Message.AfterCardEnterPlay') -> None:
        effect.GetInitiator().GetIdentity().TakeDamage(effect.this, 1, effect)

    return [
        AbilityFactory.AfterCardEnterPlay(
            AbilityType.ForcedResponse,
            CardFinder(trait="SENSE", card_type=Upgrade),
            sensory_overload,
            under_your_control=True,
        ),
        AbilityFactory.AfterUnitMakeRecovery(
            AbilityType.AlterEgoResponse,
            "You",
            DiscardThisCard,
        ),
    ]
