from . import *


def GetAbilities() -> Sequence['Ability']:
    def tracksuit_mafioso_defeated(
        effect: 'Effect',
        message: 'Message.WhenUnitBeDefeated',
    ) -> None:
        this = effect.this.CastTo(Minion)
        scheme = FindTracksuitMafia(effect)
        if scheme:
            scheme.TuckCardUnderHere(this, effect)
        elif message.killer and Unit2.IsType(message.killer):
            Faces.GiveStatus([message.killer], "Stunned", effect)
            Faces.GiveStatus([message.killer], "Confused", effect)

    return [
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            tracksuit_mafioso_defeated,
        ),
    ]
