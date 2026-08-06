from . import *


def GetAbilities() -> Sequence['Ability']:

    def can_resolve_son_of_zeus(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> bool:
        player = effect.GetInitiator()
        identity = player.GetIdentity()
        gifts = CountGifts(player)
        if identity.CanReady():
            return True
        if gifts >= 1 and player.GetControlCards(
            CardFinder(card_type=Upgrade, card_class="IdentitySpecific", canbe_ready=True),
        ):
            return True
        if gifts >= 2 and identity.CanGainTough():
            return True
        return gifts >= 3

    def son_of_zeus(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        identity = player.GetIdentity()
        Faces.ReadyAll([identity], effect)

        gifts = CountGifts(player)
        if gifts >= 1:
            upgrades = player.GetControlCards(
                CardFinder(card_type=Upgrade, card_class="IdentitySpecific", canbe_ready=True),
            )
            if upgrades:
                upgrade = player.AskChooseOneText(upgrades)
                Faces.ReadyAll([upgrade], effect)
        if gifts >= 2:
            Faces.GiveStatus([identity], "Tough", effect)
        if gifts >= 3:
            player.DrawUp(1, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            son_of_zeus,
            conditions=[can_resolve_son_of_zeus],
        ).SetPlay(),
    ]
