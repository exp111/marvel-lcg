from . import *


def GetAbilities() -> Sequence['Ability']:
    def place_acceleration(effect: 'Effect', message: 'Message2') -> None:
        Unused(message)
        effect.this.CastTo(Minion).PlaceAccelerationToken(1, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, place_acceleration),
        AbilityFactory.AfterUnitSchemeEnd(
            AbilityType.ForcedResponse,
            "This",
            place_acceleration,
        ),
    ]
