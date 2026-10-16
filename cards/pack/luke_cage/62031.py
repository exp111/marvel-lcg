from . import *

# Augmented Jaws
def GetAbilities():
    def jaws(effect,message):
        target=message.target
        if Unit2.IsType(target): target.DiscardAllTough(effect)
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="Cottonmouth"),otherwise_attach_to=Villain),
        AbilityFactory.WhenUnitWouldAttackUnit(AbilityType.ForcedInterrupt,"AttachedEnemy",Unit2,jaws),
        AbilityFactory.PlayerActionToDiscardThis(AbilityType.HeroAction).SetCost(Cost("BB")),
    ]
