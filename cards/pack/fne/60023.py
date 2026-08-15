from . import *

# Know Your Enemy


def GetAbilities() -> Sequence['Ability']:

    def know_your_enemy(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Event)
        this.RemoveThreatFromSchemes(effect.targets, 1, effect)
        this.RemoveThreatFromSchemes(effect.targets2, 1, effect)

    return [
        AbilityFactory.ReduceCostToPlayFaceWhen(
            "This",
            1,
            "You",
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().GetIdentity().HasTrait("MARTIAL ARTIST")
            ],
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            know_your_enemy,
        ).SetPlay().SetLabel("thwart")
        .SetTarget(Scheme2)
        .SetTarget2(Scheme2),
    ]
