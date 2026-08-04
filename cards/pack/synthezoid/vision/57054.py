from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        identity = message.GetDefeatingPlayer().GetIdentity()
        if not Faces.GiveStatus([identity], "Confused", effect):
            Faces.GiveStatus([identity], "Stunned", effect)

    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            defeated,
            has_defeating_player=True,
        )
    ]
