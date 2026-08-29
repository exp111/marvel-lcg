from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        *AbilityFactory.GiveKeywordToAttached(
            Identity,
            trait="HUNTED",
            ex_change_on_event=OnEvent.Form("AttachedIdentity"),
        ),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.AlterEgoAction
        ).SetCostFunc(CostFunc.DiscardDeckTopCards("YourDeck", 8)),
    ]
