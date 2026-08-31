from . import *


def GetAbilities() -> Sequence['Ability']:
    def make_deceived(
        effect: 'Effect',
        ally: 'Ally',
    ) -> None:
        from game.ability.factory.treat import TreatAsMinion

        if not ally.IsInPlay() or ally.GetCounters("threat") <= 0:
            return
        player = ally.GetControlByPlayer()

        def process(minion: 'Minion', printed_ally: 'Ally', by_effect: 'Effect') -> None:
            Unused(printed_ally)
            minion.GainTraits(1, ["DECEIVED"], by_effect)

        TreatAsMinion(
            ally,
            "Minion",
            player,
            effect,
            process=process,
            while_counter="threat",
        )

    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        allies = [
            ally for candidate in Worlds.GetOnFieldCharacters(effect)
            if Ally.IsType(candidate)
            for ally in [candidate.CastTo(Ally)]
            if ally.GetCounters("threat") == 0
        ]
        if not allies:
            return
        ally = player.AskChooseFace(
            allies,
            effect,
            forced=True,
            prompt="Choose an ally to deceive",
        )
        if ally:
            Faces.PlaceCountersOn([ally], 1, "threat", effect)
            make_deceived(effect, ally)

    def entered(effect: 'Effect', message: 'Message.AfterCardEnterPlay') -> None:
        Unused(message)
        for candidate in Worlds.GetOnFieldCharacters(effect):
            if Ally.IsType(candidate) and candidate.GetCounters("threat") > 0:
                make_deceived(effect, candidate.CastTo(Ally))

    def threat_placed(
        effect: 'Effect',
        message: 'Message.AfterCardPlacedCounter',
    ) -> None:
        if Ally.IsType(message.trigger):
            make_deceived(effect, message.trigger.CastTo(Ally))

    return [
        AbilityFactory.AfterCardEnterPlay(
            AbilityType.NonKeyword,
            "This",
            entered,
        ),
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.AfterCounterPlacedOn(
            AbilityType.NonKeyword,
            Ally,
            "threat",
            threat_placed,
        ),
    ]
