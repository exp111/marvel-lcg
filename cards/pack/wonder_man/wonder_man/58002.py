from . import *

# Ionic Physiology

def GetAbilities() -> Sequence['Ability']:

    def ionic_physiology(effect: 'Effect', message: 'Message.AfterPlayerPlayedCard') -> None:
        this = effect.this.CastTo(Upgrade)
        played_event = message.played_face.CastTo(Event)
        this.TuckCardUnderHere(played_event, effect)
        effect.GetInitiator().GetIdentity().HealthUnits(
            [effect.GetInitiator().GetIdentity()],
            1,
            effect,
        )

    return [
        AbilityFactory.AfterPlayerPlayedCard(
            AbilityType.Response,
            "You",
            Event,
            ionic_physiology,
            conditions=[
                lambda effect, message:
                    HasPrintedEnergy(message.played_face) and
                    effect.this.GetPlacedCardArea().GetSize() < 3,
            ],
        ),
    ]

