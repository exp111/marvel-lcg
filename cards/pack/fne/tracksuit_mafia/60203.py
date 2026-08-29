from . import *


def GetAbilities() -> Sequence['Ability']:
    def tracksuit_bro_defeated(
        effect: 'Effect',
        message: 'Message.WhenUnitBeDefeated',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Minion)
        scheme = FindTracksuitMafia(effect)
        if scheme:
            scheme.TuckCardUnderHere(this, effect)
        else:
            Faces.ShuffleAllTo([this], "EncounterDeck", effect)

    return [
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            tracksuit_bro_defeated,
        ),
    ]
