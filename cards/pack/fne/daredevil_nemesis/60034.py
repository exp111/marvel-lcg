from . import *


def GetAbilities() -> Sequence['Ability']:

    def deadliest_man_alive(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        message.GiveAdditionalBoostCardForThisActivation(1, effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            CardFinder(name="Bullseye", card_type=Minion),
            deadliest_man_alive,
        ),
    ]
