from . import *


def GetAbilities() -> Sequence['Ability']:
    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        Faces.GiveStatus([message.activating_enemy], "Tough", effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(HAMMERHEAD),
        *AbilityFactory.GiveKeywordToAttached("Character", stalwart=1),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.HeroAction,
        ).SetCost(Cost("YBR")).AnyPlayerCanDoThis(),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
