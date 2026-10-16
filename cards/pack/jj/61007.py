from . import *

# Piecing It All Together
def GetAbilities():
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated,"This",
        lambda effect,message: message.defeating_player.DrawUp(3,effect),has_defeating_player=True)]
