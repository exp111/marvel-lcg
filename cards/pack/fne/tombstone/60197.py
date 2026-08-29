from . import *


def GetAbilities() -> Sequence['Ability']:
    def beetle_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        this = effect.this.CastTo(Minion)
        player = message.GetToPlayer()
        attachment = Search.EncounterCard(
            effect,
            player,
            include_discard_pile=True,
            card_type=Attachment,
            check_effect_fn=lambda check_effect, face:
                face.CastTo(Attachment)._CanAttachByPrintedRuleTo(
                    this,
                    check_effect,
                ),
        )
        if attachment:
            attachment.AttachTo2(this, effect)

    return [AbilityFactory.WhenThisRevealed(None, beetle_revealed)]
