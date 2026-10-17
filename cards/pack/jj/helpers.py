from . import *


def Alias(effect):
    """Only spend evidence from the initiating player's Alias Investigations."""
    player = effect.GetInitiator()
    return next((face.CastTo(Support) for face in effect.world.FindCardsOnField(
        finder=CardFinder(name="Alias Investigations"))
        if face.GetControlBy() == player), None)


def PlaceEvidence(effect, amount):
    alias = Alias(effect)
    if alias:
        Faces.PlaceCountersOn([alias], amount, "evidence", effect)


def Suggestion(resource):
    def suggest(effect, message):
        player = effect.GetInitiator()
        def add_threat():
            effect.this.PlaceThreatOnSchemes("MainScheme", 2, effect)
        def play_or_add_threat(targets):
            if not player.PlayCardsLikeInTurn(targets, effect):
                add_threat()
        player.ChooseAbilities(effect,
            AbilityFactory.ForChoiceAbility("Play a card with the matching printed resource",
                play_or_add_threat)
                .SetTarget("YourHandCards", has_printed_res=resource, canbe_play=True),
            AbilityFactory.ForChoiceAbility("Place 2 threat on the main scheme",
                lambda targets: add_threat()),
        )
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.ForcedAction, suggest)
        .SetCostFunc(CostFunc.Exhaust("This"))
        .SetCostFunc(CostFunc.Counter("This", 1, "pheromone"))]
