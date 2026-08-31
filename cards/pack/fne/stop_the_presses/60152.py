from . import *


def GetAbilities() -> Sequence['Ability']:
    def restore_stamina(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        Unused(message)
        supports = effect.cost_func.Get(CostFunc.Exhaust).return_exhausted_cards
        Faces.PlaceCountersOn(supports, 1, "stamina", effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            restore_stamina,
        ).SetName("Restore a DAILY BUGLE support's stamina")
        .SetCostFunc(
            CostFunc.Exhaust(
                Select.From(
                    finder=DAILY_BUGLE_SUPPORT,
                    from_where=["YouControlCards"],
                )
            )
        )
        .AnyPlayerCanDoThis(),
    ]
