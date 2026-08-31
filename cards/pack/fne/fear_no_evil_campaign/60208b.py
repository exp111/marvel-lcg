from . import *
from cards.pack.fne.campaign import RAFT_PRISONERS


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        minions = [
            CardFactory.GenerateCard(card_id, None, effect.world).face
            for card_id in RAFT_PRISONERS
        ]
        if Worlds.IsExpert(effect):
            for player in Worlds.GetPlayers(effect):
                if not minions:
                    break
                minion = Rand.RandomChoice(minions, effect)
                minions.remove(minion)
                player.DealEncounterCard(minion, effect)
        Faces.ShuffleAllTo(minions, "EncounterDeck", effect)

    return [CampaignEnvironmentSetup(setup)]
