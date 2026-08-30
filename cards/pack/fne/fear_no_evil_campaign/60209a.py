from . import *
from cards.pack.fne.campaign import DAILY_BUGLE_SUPPORTS, _removed_campaign_titles


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        removed = _removed_campaign_titles(effect)
        supports = [
            CardFactory.GenerateCard(card_id, None, effect.world).face.CastTo(Support)
            for card_id in DAILY_BUGLE_SUPPORTS
            if card_id not in removed and
            CardFactory.FindCardPapers(card_id)[0].name not in removed
        ]
        for player in Worlds.GetPlayers(effect):
            if not supports:
                break
            support = player.AskChooseFace(
                supports,
                effect,
                forced=True,
                not_move=True,
                peek=True,
            )
            if support:
                supports.remove(support)
                support.PutIntoPlay(player, effect, under_control=True)

    return [CampaignEnvironmentSetup(setup)]
