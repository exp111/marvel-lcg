from . import *

# "Sweet Christmas!"
def GetAbilities():
    def eligible(effect):
        enemies=Worlds.GetVillains(effect) + Worlds.GetOnFieldMinions(effect,
            CardFinder(engaged_with=effect.GetInitiator()))
        return [face for face in enemies if face.CanBeAttackBy(effect)]
    def christmas(effect,message):
        targets=eligible(effect)
        villain=Worlds.ChooseVillain(effect,CardFinder(check_face_fn=lambda face: face in targets))
        enemies=([villain] if villain else []) + [face for face in targets if Minion.IsType(face)]
        effect.this.DealDamage(enemies,5,effect)
    return [
        AbilityFactory.ReduceCostToPlayThis(lambda effect: effect.GetInitiator().GetIdentity().tough),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,christmas,
            conditions=[lambda effect,message: effect.GetInitiator().GetIdentity().IsStunned() or bool(eligible(effect))])
            .SetPlay().SetLabel("attack"),
    ]
