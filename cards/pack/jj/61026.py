from . import *

# Joys of Life
def GetAbilities():
    def joys(effect,message):
        effect.GetInitiator().ChooseAbilities(effect,
            AbilityFactory.ForChoiceAbility("Exhaust a Civilian alter-ego to ready a hero or ally",
                lambda targets: Faces.ReadyAll(targets,effect))
            .SetCostFunc(CostFunc.Exhaust(CardFinder(card_type=AlterEgo,trait="CIVILIAN")))
            .SetTarget(Hero|Ally,canbe_ready=True),
            AbilityFactory.ForChoiceAbility("Exhaust a hero or ally to ready a Civilian alter-ego",
                lambda targets: Faces.ReadyAll(targets,effect))
            .SetCostFunc(CostFunc.Exhaust(CardFinder(card_type=Hero|Ally)))
            .SetTarget(AlterEgo,trait="CIVILIAN",canbe_ready=True))
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,joys).SetPlay()]
