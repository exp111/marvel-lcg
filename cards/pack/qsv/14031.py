from . import *

# United We Stand

def GetAbilities() -> Sequence['Ability']:

    def get_villain_stage(effect: 'Effect') -> int:
        villain = Worlds.ChooseVillain(
            effect,
            prompt="Choose a villain for United We Stand's stage value",
        )
        return villain.printed_stage if villain else 0

    def united_we_stand(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Event)
        Unused(this)

        this.HealthUnits(effect.targets, 1, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            united_we_stand,
        ).SetPlay(only_if_your_identity_has_trait="AVENGER")
        .SetTarget(Friend, canbe_heal=True,
            range=(1, lambda effect: min(3, get_villain_stage(effect))))
    ]

