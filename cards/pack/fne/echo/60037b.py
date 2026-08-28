from . import *


def GetAbilities() -> Sequence['Ability']:
    def maya_lopez(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldChangeForm',
    ) -> None:
        player = effect.GetInitiator()
        face = Search.PlayerCard(
            effect,
            player,
            include_player_deck=True,
            card_type=Event,
            card_classes=["Aspect", "Basic"],
        )
        if face:
            player.GainCard(face, effect)

    return [
        AbilityFactory.WhenUnitWouldChangeForm(
            AbilityType.Interrupt,
            "You",
            maya_lopez,
            to_form=Hero,
        ),
        *DaredevilEventDiscountAbilities(),
    ]
