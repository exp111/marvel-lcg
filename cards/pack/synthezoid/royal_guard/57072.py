from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        *AbilityFactory.GiveKeywordToAttached(Identity, trait="HUNTED"),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.AlterEgoAction
        ).SetCostFunc(CostFunc.DiscardDeckTopCards("YourDeck", 8)),
    ]
