from . import *


def GetAbilities() -> Sequence['Ability']:
    def ben_urich(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        Unused(message)
        player = effect.GetInitiator()
        faces = player.LookAtDeck("EncounterDeck", 2, effect)
        player.MayChooseOneAbility(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Discard 1 of those encounter cards",
                lambda targets: Faces.DiscardAll(targets, effect),
            ).SetTarget(
                faces,
                by_search=True,
                not_move=True,
                not_shuffle=True,
                display_in_target_order=True,
            ),
        )

    ability = AbilityFactory.WhenInYourPlayTurn(AbilityType.Action, ben_urich)
    for cost in StaminaCost():
        ability.SetCostFunc(cost)
    return [ability]
