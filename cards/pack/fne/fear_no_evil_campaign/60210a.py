from . import *


def GetAbilities() -> Sequence['Ability']:
    return [FlipAfterYouReveal(Minion)]
