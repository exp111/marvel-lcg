from . import *


def GetAbilities() -> Sequence['Ability']:
    def kingpin(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        this = effect.this.CastTo(Minion)
        message.SetBeInstead(effect)
        this.DoSchemes(message.against_player, effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            "This",
            kingpin,
            against_player=PlayerFinder(name="Maya Lopez"),
        ),
    ]
