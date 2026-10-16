from . import *

# Size Advantage
def GetAbilities():
    def size_advantage(effect,message):
        identity=effect.GetInitiator().GetIdentity()
        for target in effect.targets:
            amount=6 if identity.HasTrait("GIANT") or identity.health>target.CastTo(Unit2).health else 3
            effect.this.DealDamage([target],amount,effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,size_advantage)
        .SetPlay().SetLabel("attack").SetTarget(Enemy)]
