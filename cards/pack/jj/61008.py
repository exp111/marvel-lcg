from . import *

# Calling in Favors
def GetAbilities():
    def calling_in_favors(effect, message):
        player=effect.GetInitiator()
        ally=Search.PlayerCard(effect, player, include_player_deck=True, card_type=Ally, not_move=True)
        if ally:
            player.PlayCardsLikeInTurn([ally], effect, update_resources_cost=-2)
        player.player_deck.Shuffle(effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction, calling_in_favors)
        .SetCostFunc(CostFunc.Exhaust("This"))
        .SetCostFunc(CostFunc.Counter(Select.From(CardFinder(name="Alias Investigations"), from_where=["YourPlayArea"]), 2, "evidence"))]
