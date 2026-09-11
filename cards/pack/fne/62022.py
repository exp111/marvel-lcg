from . import *

# Dynamic Duo

def GetAbilities() -> Sequence['Ability']:

    def dynamic_duo(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        initiator = effect.GetInitiator()

        # Keep both selections in place until the search is complete, then
        # add the found cards to hand and shuffle the deck exactly once.
        team_up_card = Search.PlayerCard(
            effect,
            initiator,
            include_player_deck=True,
            include_discard_pile=True,
            not_move=True,
            check_face_fn=lambda face: HasTeamUp.IsType(face) and "TeamUp" in face.paper.desc,
        )
        if team_up_card:
            has_team_up = team_up_card.CastTo(HasTeamUp)
            ally_names = [name for names in has_team_up.team_up for name in names]
            ally = Search.PlayerCard(
                effect,
                initiator,
                include_player_deck=True,
                include_discard_pile=True,
                not_move=True,
                card_type=Ally,
                names=ally_names,
            )
            cards_to_add = [team_up_card]
            if ally:
                cards_to_add.append(ally)
            Faces.AddToHand(cards_to_add, initiator, effect)

        # Searching the deck requires a shuffle even if nothing was found
        # there, including when both selected cards came from the discard pile.
        initiator.player_deck.Shuffle(effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            dynamic_duo,
        ).SetPlay(),
    ]
