from . import *

# Work-Life Balance
def GetAbilities():
    def balance(effect,message):
        player=effect.GetInitiator()
        player.ChooseAbilities(effect,
            AbilityFactory.ForChoiceAbility("Remove an ally you control from the game",
                lambda targets: Faces.RemoveAllFromGame([effect.this],effect))
                .SetCostFunc(CostFunc.RemoveFromGame("YourAlly")),
            AbilityFactory.ForChoiceAbility("Confuse your identity",
                lambda targets: confuse(effect)).SetTarget("YourIdentity",canbe_confused=True))
    def confuse(effect):
        if Faces.GiveStatus([effect.GetInitiator().GetIdentity()],"Confused",effect):
            Faces.DiscardAll([effect.this],effect)
    return [
        AbilityFactory.AdditionalCostToChangeForm("You",CostFunc.Discard("YourHandCards")),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction,balance),
    ]
