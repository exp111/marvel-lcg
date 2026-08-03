from . import *

def GetAbilities() -> Sequence['Ability']:
    def dart(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.GainPiercing(effect)
        message.GainRanged(effect)
        RunAt.AfterEnemyActivationEnd(effect, message, lambda: Faces.DiscardAll([effect.this], effect))
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(name="Moon Knight"), otherwise_attach_to="EnemyLeader"
        ),
        *AbilityFactory.GiveKeywordToAttached(Enemy, attack=2),
        AbilityFactory.WhenUnitWouldAttack(AbilityType.ForcedInterrupt, "AttachedCharacter", dart),
    ]
