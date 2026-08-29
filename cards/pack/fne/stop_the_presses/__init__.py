from cards.pack import *


DAILY_BUGLE_SUPPORT = CardFinder(
    trait="DAILY BUGLE",
    card_type=Support,
    set_name="Stop the Presses!",
)


def GetDailyBugleSupports(effect: 'Effect', *, player: 'Player|None'=None) -> List['Support']:
    supports = [
        face.CastTo(Support)
        for face in Worlds.FindCardsOnField(effect, DAILY_BUGLE_SUPPORT)
    ]
    if player is not None:
        supports = [face for face in supports if face.GetControlBy() == player]
    return supports


def StaminaCost(target: 'CardFace|Literal["This"]'="This") -> List['CostFunc.Base']:
    return [
        CostFunc.Exhaust(target),
        CostFunc.Counter(target, 1, "stamina"),
    ]


def ExhaustAndRemoveStaminaCost(supports: Sequence['Support']) -> 'CostFunc.Custom':
    selector = Select.From(
        faces=supports,
        range=(1, 1),
        not_move=True,
        not_shuffle=True,
    )
    selector.selector_filter.AddParameter(
        canbe_exhaust=True,
        check_effect_fn=lambda effect, face: face.GetCounters("stamina") > 0,
    )

    def pay(targets: Sequence['CardFace'], effect: 'Effect') -> bool:
        if len(targets) != 1 or Faces.ExhaustAll(targets, effect) != list(targets):
            return False
        return targets[0].RemoveCountersInternal(
            1,
            "stamina",
            effect,
            forced=False,
        ) is not None

    return CostFunc.Custom(selector, pay)
