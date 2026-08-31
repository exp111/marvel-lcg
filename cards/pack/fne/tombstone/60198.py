from . import *


def GetAbilities() -> Sequence['Ability']:
    def tombstone_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        Unused(message)
        villain = Worlds.FindVillain(effect)
        if villain:
            Faces.GiveStatus([villain], "Tough", effect)

    return [AbilityFactory.WhenCardBecomeBoost("This", tombstone_boost)]
