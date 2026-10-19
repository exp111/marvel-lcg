from . import *

# S.H.I.E.L.D. Recruits

def GetAbilities() -> Sequence['Ability']:

    def shield_recruits_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(MainScheme)
        Unused(this)

        team = Worlds.GetEnemyTeam(effect)
        faces = Search.SearchForCards(
            effect,
            team,
            include_encounter_deck=True,
            range=Select.ExactTargetCountUpToAvailable(Worlds.GetYourTeamSize(effect)),
            card_type=Minion
        )

        def action(player: 'Player'):
            if faces:
                face = faces.pop()
                player.DealEncounterCard(face, effect)

        Players.ForEachPlayer(effect, action)


    return [
        AbilityFactory.ThisGainKeyword(
            check_fn=lambda effect, ui:
                Worlds.GetYourTeamSize(effect) > 1,
            hinder="2*",
        ),
        AbilityFactory.WhenThisRevealed(
            None,
            shield_recruits_revealed
        ),
    ]

