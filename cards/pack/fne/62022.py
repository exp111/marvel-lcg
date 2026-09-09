
from . import *

# Dynamic Duo

def GetAbilities() -> Sequence['Ability']:

    def dynamic_duo(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        initiator = effect.GetInitiator()

        # Step 1: search deck + discard for any Team-Up card
        team_up_card = Search.PlayerCard(
            effect,
            initiator,
            include_player_deck=True,
            include_discard_pile=True,
            check_face_fn=lambda face: HasTeamUp.IsType(face) and "TeamUp" in face.paper.desc,
        )
        if not team_up_card:
            return

        # Step 2: read the two character names from the found Team-Up card
        has_team_up = team_up_card.CastTo(HasTeamUp)
        ally_names = [name for names in has_team_up.team_up for name in names]

        # Step 3: search deck + discard for an ally matching either name
        ally = Search.PlayerCard(
            effect,
            initiator,
            include_player_deck=True,
            include_discard_pile=True,
            card_type=Ally,
            names=ally_names,
        )

        # Step 4: add both to hand
        cards_to_add = [c for c in [team_up_card, ally] if c is not None]
        if cards_to_add:
            Faces.AddToHand(cards_to_add, initiator, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            dynamic_duo,
        ).SetPlay(),
    ]
