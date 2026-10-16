from . import *

# Knuckle Sandwich
def GetAbilities():
    def sandwich(effect,message):
        effect.this.DealDamage(effect.targets,3,effect)
        player=effect.GetInitiator()
        identity=player.GetIdentity()
        if identity.tough and player.MayChooseOneText(["Discard 1 tough status card to return Knuckle Sandwich to your hand"]):
            identity.DiscardTough(effect,rule=1)
            player.GainCard(effect.this,effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,sandwich)
        .SetPlay().SetLabel("attack").SetTarget(Enemy)]
