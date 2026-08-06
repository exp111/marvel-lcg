from . import *

def GetAbilities() -> Sequence['Ability']:
    def scheme(effect: 'Effect', message: 'Message.WhenUnitWouldScheme') -> None:
        RunAt.AfterEnemyActivationEnd(effect, message, lambda: Faces.DiscardAll([effect.this], effect))
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="She-Hulk", card_type=Leader)),
        *AbilityFactory.GiveKeywordToAttached(Leader, stalwart=1),
        AbilityFactory.WhenUnitWouldScheme(AbilityType.ForcedInterrupt, "AttachedCharacter", scheme),
        AbilityFactory.WhenCardBecomeBoost("This", RevealThisCard),
    ]
