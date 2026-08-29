from . import *


def GetAbilities() -> Sequence['Ability']:
    def daredevil(
        effect: 'Effect',
        message: 'Message.AfterUnitUseBasicPower',
    ) -> None:
        identity = effect.GetInitiator().GetIdentity()
        identity.GetBuff(BuffDaredevilEventDiscount).Add()

    return [
        AbilityFactory.AfterUnitUseBasicPower(
            AbilityType.Response,
            "This",
            daredevil,
        ),
    ]
