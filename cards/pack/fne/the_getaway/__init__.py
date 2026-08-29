from cards.pack import *


GETAWAY_SCHEME = CardFinder(name="The Getaway", card_type=MainScheme)


def GetGetawayScheme(effect: 'Effect') -> 'MainScheme|None':
    scheme = Worlds.FindCardOnField(effect, GETAWAY_SCHEME)
    return scheme.CastTo(MainScheme) if scheme else None


def GetSpeed(effect: 'Effect', ui: List['CardFace']|None=None) -> int:
    scheme = GetGetawayScheme(effect)
    if not scheme:
        return 0
    if ui is not None:
        ui.append(scheme)
    return scheme.GetCounters("speed")


def SpeedThreshold(threshold: int) -> Callable[['Effect', List['CardFace']], int]:
    return lambda effect, ui: int(GetSpeed(effect, ui) >= threshold)


SPEED_EVENT = OnEvent.Counter(GETAWAY_SCHEME, "speed")
