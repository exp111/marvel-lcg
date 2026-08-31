from . import *


def GetAbilities() -> Sequence['Ability']:
    def defeated_character(
        effect: 'Effect',
        message: 'Message.AfterUnitDefeatedUnit',
    ) -> None:
        effect.this.HealthUnits([message.killer], 1, effect)
        PlaceThreatHere(effect, 1)

    def defeated_scheme(
        effect: 'Effect',
        message: 'Message.AfterUnitDefeatedScheme',
    ) -> None:
        effect.this.HealthUnits([message.killer], 1, effect)
        PlaceThreatHere(effect, 1)

    return [
        AbilityFactory.AfterUnitDefeatedUnit(
            AbilityType.ForcedResponse,
            Unit2,
            Unit2,
            defeated_character,
            conditions=[
                lambda effect, message: IsInThisPlayArea(message.killer, effect),
            ],
        ),
        AbilityFactory.AfterUnitDefeatedScheme(
            AbilityType.ForcedResponse,
            Unit2,
            SchemeSide2,
            defeated_scheme,
            conditions=[
                lambda effect, message: IsInThisPlayArea(message.killer, effect),
            ],
        ),
        *ProtectionRacketLossAbilities(),
    ]
