from cards.pack import *

def PlaceDeckTopCardFacedownUnderOperationZeroTolerance(player: 'Player', effect: 'Effect'):
    face = player.player_deck.Get(True)[0]
    PlaceCardFacedownUnderOperationZeroTolerance(face, effect)

def PlaceCardFacedownUnderOperationZeroTolerance(face: 'CardFace', effect: 'Effect'):
    scheme = Worlds.FindCardOnField(
        effect,
        name="Operation Zero Tolerance",
        card_type=SchemeSide2
    )
    if scheme:
        scheme.PlaceCardHere(face, False, effect)

def SetupProjectWideawakeModularDifficulty(effect: 'Effect') -> 'Effect|None':
    def place_captured_cards(count: int) -> None:
        chooser = Worlds.GetFirstPlayer(effect)
        players = Worlds.GetPlayers(effect)

        for _ in range(count):
            abilities = [
                AbilityFactory.ForChoiceAbility(
                    f"Place the top card of {player.name}'s deck facedown under Operation Zero Tolerance",
                    lambda targets, player=player:
                        PlaceDeckTopCardFacedownUnderOperationZeroTolerance(
                            player,
                            effect,
                        ),
                )
                for player in players
            ]
            chooser.ChooseAbilities(effect, *abilities)

    return ModularDifficulty.MayApply(
        effect,
        description=lambda count:
            f"Place {count} facedown {'card' if count == 1 else 'cards'} "
            "under Operation Zero Tolerance (modular difficulty)",
        operation=place_captured_cards,
        per_player=False,
    )
