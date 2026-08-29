from . import *

# Art Thief


def GetAbilities() -> Sequence['Ability']:
    def art_thief_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()
        villain = Worlds.FindVillain(effect)
        attachment = Search.EncounterCard(
            effect,
            player,
            include_discard_pile=True,
            trait="ART",
            card_type=Attachment,
        )
        if villain and attachment:
            attachment.AttachTo2(villain, effect)
        else:
            MoveArtFromIdentityToVillain(effect, player)

    def art_thief_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        MoveArtFromIdentityToVillain(effect, message.GetToPlayer())

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            art_thief_revealed,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            art_thief_boost,
        ),
    ]
