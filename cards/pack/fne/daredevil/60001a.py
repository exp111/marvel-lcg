from . import *


def GetAbilities() -> Sequence['Ability']:

    def superhuman_senses(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        ChooseAndPlaySenseUpgrade(
            effect.GetInitiator(),
            effect,
            top_only=True,
        )

    def top_sense_can_be_played(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> bool:
        player = effect.GetInitiator()
        top = GetSenseDeck(player).GetTop()
        return bool(top and GetSenseAttachmentTargets(top, effect))

    return [
        *SenseDeckRuleAbilities(),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            superhuman_senses,
            conditions=[top_sense_can_be_played],
        ).SetName("Superhuman Senses"),
    ]
