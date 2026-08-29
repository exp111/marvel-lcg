from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        nemesis = Worlds.FindCardOnField(
            effect,
            CardFinder(card_type=Minion, is_nemesis=player),
        )
        if nemesis:
            nemesis.CastTo(Minion).DoActivate(player, effect)
            return
        nemesis = Find.Find(
            effect,
            who_perform=player,
            finder=CardFinder(card_type=Minion, is_nemesis=player),
        )
        if nemesis:
            nemesis.Reveal(player, effect)
        else:
            RevealUnderlingNotInPlay(player, effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        message.would_atk_message.GainOverKill(effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            during_attack=True,
        ),
    ]
