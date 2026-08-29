from . import *

# Move in Shadow


def GetAbilities() -> Sequence['Ability']:

    def move_in_shadow(effect: 'Effect', message: 'Message.AfterPlayerPlayedCard') -> None:
        effect.this.CastTo(Upgrade).RemoveThreatFromSchemes(
            effect.targets,
            1,
            effect,
        )

    return [
        AbilityFactory.ReduceCostToPlayFaceWhen(
            "This",
            1,
            "You",
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().GetIdentity().HasTrait("MARTIAL ARTIST", "SPY")
            ],
        ),
        AbilityFactory.CanPlayThisUpgradeCard(),
        AbilityFactory.AfterPlayerPlayedCard(
            AbilityType.Response,
            "You",
            CardFace,
            move_in_shadow,
        ).SetLabel("thwart")
        .SetTarget(Scheme2),
    ]
