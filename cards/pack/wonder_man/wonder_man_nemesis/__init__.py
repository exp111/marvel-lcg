from cards.pack.wonder_man import *


def ActivateGrimReaper(effect: 'Effect', player: 'Player') -> bool:
    result = Worlds.Enemies.AllMinionActivateAgainstYou(
        effect,
        player,
        finder=CardFinder(name="Grim Reaper"),
    )
    # Callers need to know whether Grim Reaper is in play, not whether the
    # activation ultimately happened. A stunned Grim Reaper, for example, is
    # still in play and must not cause an "otherwise" effect to resolve.
    return result.has_enemy

