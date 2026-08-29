from . import *


def GetAbilities() -> Sequence['Ability']:
    def improvisation(
        effect: 'Effect',
        message: 'Message.AfterPlayerPlayedCard',
    ) -> None:
        this = effect.this.CastTo(Upgrade)
        player = effect.GetInitiator()
        event = message.played_face.CastTo(Event)

        if event.HasTrait("ATTACK"):
            identity = player.GetIdentity()
            identity.HealthUnits([identity], 1, effect)

        if event.HasTrait("DEFENSE"):
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    "Remove 1 threat from a scheme",
                    lambda targets:
                        this.RemoveThreatFromSchemes(targets, 1, effect),
                ).SetTarget(Scheme2),
            )

        if event.HasTrait("THWART"):
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    "Deal 1 damage to an enemy",
                    lambda targets:
                        this.DealDamage(targets, 1, effect),
                ).SetTarget(Enemy),
            )

    return [
        AbilityFactory.AfterPlayerPlayedCard(
            AbilityType.HeroResponse,
            "You",
            Event,
            improvisation,
            conditions=[
                lambda effect, message:
                    message.played_face.HasTrait("ATTACK", "DEFENSE", "THWART"),
            ],
        ).SetName("Improvisation"),
    ]
