from . import *

# De-escalation


def GetAbilities() -> Sequence['Ability']:

    def de_escalation(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        faces = Worlds.GetAccelerationTokenFaces(effect)
        face = Filter.One(faces, effect)
        if face:
            Faces.RemoveTokensOn([face], 1, "acceleration_token", effect)

    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            de_escalation,
        ),
    ]
