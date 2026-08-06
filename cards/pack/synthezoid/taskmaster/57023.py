from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(name="Taskmaster"), otherwise_attach_to="EnemyLeader"
        ),
        AbilityFactory.UnitAttackGainKeyword("Attached", piercing=True),
        AbilityFactory.PlayerActionToDiscardThis(AbilityType.HeroAction).SetCost(Cost("BR")),
    ]
