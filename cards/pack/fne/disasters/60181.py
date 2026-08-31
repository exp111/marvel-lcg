from . import *


def GetAbilities() -> Sequence['Ability']:
    def choose_disaster(player: 'Player', effect: 'Effect') -> 'Environment|None':
        environments = Worlds.FindCardsOnField(
            effect,
            trait="DISASTER",
            card_type=Environment,
        )
        return player.AskChooseFace(
            environments,
            effect,
            prompt="Choose a DISASTER environment",
            forced=True,
        ) if environments else None

    def place_civilian(player: 'Player', effect: 'Effect') -> bool:
        environment = choose_disaster(player, effect)
        return bool(
            environment
            and Faces.PlaceCountersOn([environment], 1, "civilian", effect)
        )

    def bystanders_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()
        if place_civilian(player, effect):
            return
        environment = Search.EncounterCard(
            effect,
            player,
            include_discard_pile=True,
            trait="DISASTER",
            card_type=Environment,
        )
        if environment:
            environment.Reveal(player, effect)

    def bystanders_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        place_civilian(message.GetToPlayer(), effect)

    return [
        AbilityFactory.WhenThisRevealed(None, bystanders_revealed),
        AbilityFactory.WhenCardBecomeBoost("This", bystanders_boost),
    ]
