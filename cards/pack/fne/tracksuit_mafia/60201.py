from . import *


def GetAbilities() -> Sequence['Ability']:
    def the_clown_schemes(
        effect: 'Effect',
        message: 'Message.AfterUnitSchemeEnd',
    ) -> None:
        Unused(message)
        Faces.GiveFacedownBoostCards([effect.this], 1, effect)

    return [
        AbilityFactory.AfterUnitSchemeEnd(
            AbilityType.ForcedResponse,
            "This",
            the_clown_schemes,
        ),
    ]
