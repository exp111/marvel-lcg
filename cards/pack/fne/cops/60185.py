from . import *

# Police Cordon


def GetAbilities() -> Sequence['Ability']:
    def police_cordon_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()
        minion = Search.EncounterCard(
            effect,
            player,
            include_discard_pile=True,
            trait="POLICE",
            card_type=Minion,
        )
        if minion:
            minion.Reveal(player, effect)

    return [
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            CardFinder(trait="POLICE", card_type=Minion),
            guard=1,
            patrol=1,
        ),
        AbilityFactory.WhenThisRevealed(
            None,
            police_cordon_revealed,
        ),
    ]
