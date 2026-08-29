from . import *

# Gene Pool

def GetAbilities() -> Sequence['Ability']:

    def gene_pool_setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        Unused(this)

        ModularDifficulty.MayApply(
            effect,
            description=lambda threat:
                f"Place {threat} threat on Gene Pool (modular difficulty)",
            operation=lambda threat:
                this.PlaceThreatOnSchemes([this], threat, effect),
            per_player=True,
        )

    def gene_pool(effect: 'Effect', message: 'Message.AfterUnitBeDefeated') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        Unused(this)

        this.PlaceThreatOnSchemes([this], 3, effect)


    return [
        AbilityFactory.WhenCardSetup(
            "This",
            gene_pool_setup,
        ),
        AbilityFactory.AfterUnitBeDefeated(
            AbilityType.ForcedResponse,
            Ally,
            gene_pool,
            by_consequential=False,
        ),
    ]

