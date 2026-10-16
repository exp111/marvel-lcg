from . import *

# "Sweet Christmas!"
def GetAbilities():
    def christmas(effect,message):
        player=effect.GetInitiator()
        enemies=[*Worlds.GetVillains(effect),*Worlds.GetOnFieldMinions(effect,CardFinder(engaged_with=player))]
        effect.this.DealDamage(enemies,5,effect)
    return [
        AbilityFactory.ReduceCostToPlayThis(lambda effect: effect.GetInitiator().GetIdentity().tough),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,christmas).SetPlay().SetLabel("attack"),
    ]
