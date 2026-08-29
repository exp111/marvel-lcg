from . import *


def GetAbilities() -> Sequence['Ability']:
    def protect(effect: 'Effect', player: 'Player') -> None:
        villain = Worlds.FindVillain(effect)
        if villain:
            Faces.GiveStatus([villain], "Tough", effect)

    return PurpleCommandAbility("Exhaust this card and remove 1 command counter → give the villain a tough status card", protect)
