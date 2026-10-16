from . import *

# Strategy Session
def GetAbilities():
    def session(effect,message):
        player=effect.targets[0].GetControlByPlayer()
        face=Search.PlayerCard(effect,player,include_player_deck=True,card_type=PlayerSideScheme)
        if face: player.GainCard(face,effect)
    return [
        AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction,session).SetPlay().SetTarget("Players"),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,
            lambda effect,message: effect.this.RemoveThreatFromSchemes(effect.targets,3,effect))
        .SetPlay().SetLabel("thwart").SetTarget(PlayerSideScheme),
    ]
