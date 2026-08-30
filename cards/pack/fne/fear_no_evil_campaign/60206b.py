from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        for player in Worlds.GetPlayers(effect):
            attachment = Search.EncounterCard(
                effect,
                player,
                include_discard_pile=False,
                card_type=Attachment,
            )
            if attachment:
                attachment.Reveal(player, effect)
            else:
                player.DealEncounterCards(1, effect)

    def cannot_discard_first_round(
        effect: 'Effect',
        message: 'Message.WhenCardWouldMoveToArea',
    ) -> None:
        message.SetCannot(effect)

    return [
        CampaignEnvironmentSetup(setup),
        AbilityFactory.WhenCardWouldMoveToArea(
            AbilityType.NonKeyword,
            Attachment,
            cannot_discard_first_round,
            from_play=True,
            into_discard_pile=True,
            conditions=[
                lambda effect, message: Worlds.IsExpert(effect),
                lambda effect, message: effect.world.round_id <= 1,
            ],
        ).SetName("Attachments cannot be discarded during the first round"),
    ]
