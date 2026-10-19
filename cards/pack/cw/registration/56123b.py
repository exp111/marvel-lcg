from . import *

# The Initiative

def GetAbilities() -> Sequence['Ability']:

    def the_initiative_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(MainScheme)
        Unused(this)

        team = Worlds.GetEnemyTeam(effect)
        faces = Search.SearchForCards(
            effect,
            team,
            include_encounter_deck=True,
            include_encounter_discard_pile=True,
            range=Select.ExactTargetCountUpToAvailable(Worlds.GetYourTeamSize(effect)),
            card_type=SchemeSide2
        )

        def action(player: 'Player'):
            if faces:
                face = faces.pop()
                player.DealEncounterCard(face, effect)

        Players.ForEachPlayer(effect, action)


    return [
        AbilityFactory.WhenThisRevealed(
            None,
            the_initiative_revealed
        ),
    ]

