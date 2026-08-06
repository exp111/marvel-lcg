from . import *

# * Sentry: Robert Reynolds

def GetAbilities() -> Sequence['Ability']:

    def sentry(effect: 'Effect', message: 'Message.AfterCardEnterPlay') -> None:
        this = effect.this.CastTo(Ally)
        Unused(this)

        initiator = effect.GetInitiator()

        def place_fallback_threat() -> None:
            this.PlaceThreatOnSchemes("MainScheme", 6, effect)

        scheme = Search.EncounterCard(
            effect,
            initiator,
            include_discard_pile=False,
            card_type=SchemeSide2
        )
        if scheme:
            revealed = scheme.Reveal(
                initiator,
                effect,
                if_no_entered_play=place_fallback_threat,
            )
            if revealed is None:
                place_fallback_threat()
        else:
            place_fallback_threat()


    return [
        AbilityFactory.AfterCardEnterPlay(
            AbilityType.ForcedResponse,
            "This",
            sentry
        ),
    ]
