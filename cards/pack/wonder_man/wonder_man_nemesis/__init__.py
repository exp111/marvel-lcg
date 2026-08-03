from cards.pack.wonder_man import *


def ActivateGrimReaper(effect: 'Effect', player: 'Player') -> bool:
    result = Worlds.Enemies.AllMinionActivateAgainstYou(
        effect,
        player,
        finder=CardFinder(name="Grim Reaper"),
    )
    return result.activated_cnt > 0

