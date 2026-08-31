from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        supports = GetDailyBugleSupports(effect)
        choices: List[Ability] = []
        if any(support.CanExhaust() and support.GetCounters("stamina") > 0 for support in supports):
            remove = AbilityFactory.ForChoiceAbility(
                "Exhaust a DAILY BUGLE support and remove 1 stamina counter",
            )
            remove.SetCostFunc(ExhaustAndRemoveStaminaCost(supports))
            choices.append(remove)

        scheme = Worlds.FindMainScheme(effect, against_player=player)
        if scheme:
            choices.append(
                AbilityFactory.ForChoiceAbility(
                    "Place 2 threat on the main scheme",
                    lambda targets: scheme.PlaceThreatOnSchemes([scheme], 2, effect),
                )
            )
        if choices:
            player.ChooseAbilities(effect, *choices)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        supports = [support for support in GetDailyBugleSupports(effect) if support.CanExhaust()]
        if not supports:
            return
        chosen = player.AskChooseFace(
            supports,
            effect,
            forced=True,
            prompt="Choose a DAILY BUGLE support to exhaust",
        )
        if chosen:
            Faces.ExhaustAll([chosen], effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
