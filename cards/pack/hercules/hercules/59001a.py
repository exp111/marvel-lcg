from . import *


def GetAbilities() -> Sequence['Ability']:

    def atonement(effect: 'Effect', message: 'Message.AfterCardsMoved') -> None:
        player = effect.GetInitiator()

        def finish_atonement() -> None:
            Faces.ReadyAll([player.GetIdentity()], effect)
            YouMayFlipToYourAlterEgoForm(player, effect)

        deck = GetGiftDeck(player)
        if deck:
            gift = deck.GetTop()
            if gift:
                # A GIFT can open its own response window when it enters play.
                # Finish Atonement at the end of that event so the nested
                # response cannot consume the ready and optional form change.
                RunAt.AfterFaceEnterPlay(effect, gift, finish_atonement)
                gift.PutIntoPlay(player, effect, under_control=True)
                return

        finish_atonement()

    return [
        AbilityFactory.AfterCardsMoved(
            AbilityType.Response,
            CardFinder(trait="LABOR"),
            atonement,
            conditions=[
                lambda effect, message:
                    Worlds.VictoryDisplay(effect) in message.into_areas,
            ],
        ).SetName("Atonement").LimitOncePerPhase(),
    ]
