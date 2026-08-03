from . import *

def GetAbilities() -> Sequence['Ability']:
    def attack(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.GainOverKill(effect)
        RunAt.AfterEnemyActivationEnd(effect, message, lambda: Faces.DiscardAll([effect.this], effect))
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="She-Hulk", card_type=Leader)),
        *AbilityFactory.GiveKeywordToAttached(Leader, attack=2),
        AbilityFactory.WhenUnitWouldAttack(AbilityType.ForcedInterrupt, "AttachedCharacter", attack),
        AbilityFactory.WhenCardBecomeBoost("This", RevealThisCard),
    ]
