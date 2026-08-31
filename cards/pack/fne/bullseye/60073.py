from . import *

# Deranged Bloodlust


def GetAbilities() -> Sequence['Ability']:
    def deranged_bloodlust_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(EncounterSideScheme)
        bullseye = Worlds.FindCardOnField(effect, BULLSEYE)
        if bullseye and Villain.IsType(bullseye):
            this.PlaceThreatOnSchemes(
                [this],
                bullseye.printed_stage,
                effect,
            )

    def deranged_bloodlust_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        player = message.GetToPlayer()
        message.AfterThisActivation(
            effect,
            lambda: this.Reveal(player, effect),
        )

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            deranged_bloodlust_revealed,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            deranged_bloodlust_boost,
        ),
    ]
