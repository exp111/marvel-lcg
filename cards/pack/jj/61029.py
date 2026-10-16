from . import *

# Defend Our City
def GetAbilities():
    def defend_city(effect,message):
        def search(player):
            face=Search.PlayerCard(effect,player,include_player_deck=True,include_discard_pile=True,
                may=True,check_face_fn=lambda face: "TeamUp" in face.paper.desc)
            if face: player.GainCard(face,effect)
        Players.ForEachPlayer(effect,search)
        # The discount continues after this scheme moves to the victory display.
        effect.this.effect.RegisterTemp(AbilityFactory.ReduceCostToPlayFaceWhen(
            CardFinder(check_face_fn=lambda face: "TeamUp" in face.paper.desc),1,"EachPlayer").NoOutOfPlayLimit(),
            unregister_after_exec=False,until_phase_end=True)
    return [AbilityFactory.CanPlayThisSchemeCard().SetPlay(only_if_your_identity_has_trait="DEFENDER"),
        AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated,"This",defend_city)]
