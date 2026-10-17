from . import *

# Grapnel Launcher


def GetAbilities():
    def grapnel(effect, message):
        effect.GetInitiator().GetHero().MakeGrantedBasicThwart(
            effect, thwart_bonus=1, ignore_keywords=("Patrol", "Crisis"),
        )

    return [AbilityFactory.WhenInYourPlayTurn(
        AbilityType.HeroAction, grapnel,
        conditions=[lambda effect, message:
            effect.GetInitiator().GetHero().CanMakeGrantedBasicThwart(
                effect, ignore_keywords=("Patrol", "Crisis"),
            )],
    ).SetName("Grapnel Launcher").SetCostFunc(CostFunc.Discard("This"))
     .SetIgnoreKeyword("Patrol", "Crisis")]
