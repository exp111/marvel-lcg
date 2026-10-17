from . import *

# Augmented Jaws
def GetAbilities():
    def jaws(effect,message):
        target=message.target
        if Unit2.IsType(target): target.DiscardAllTough(effect)
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="Cottonmouth"),
            otherwise_attach_to=Select.From(CardFinder(card_type=Villain,
                check_effect_fn=lambda effect, face: face == Worlds.FindVillain(effect)))),
        AbilityFactory.WhenUnitWouldAttackUnit(AbilityType.ForcedInterrupt,"AttachedEnemy",Unit2,jaws),
        AbilityFactory.PlayerActionToDiscardThis(AbilityType.HeroAction).SetCost(Cost("BB")),
    ]
