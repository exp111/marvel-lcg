from . import *


def GetAbilities() -> Sequence['Ability']:
    def collapsing_bridge(
        effect: 'Effect',
        message: 'Message.AfterSchemeRemoveThreat',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(EncounterSideScheme)
        this.PlaceThreatOnSchemes([this], 1, effect)

    return [
        AbilityFactory.AfterSchemeRemoveThreat(
            AbilityType.ForcedResponse,
            "This",
            collapsing_bridge,
        ),
    ]
