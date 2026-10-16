from . import *

# Righteous Purpose
def GetAbilities():
    return [
        AbilityFactory.CanPlayThisSupportCard(under_any_players_control=True),
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(Friend,control_by="You",
            get_new_value=lambda effect,face: int(face.CastTo(Unit2).health==1),
            attack=2,thwart=2,change_on_event=OnEvent.Health(Friend)),
    ]
