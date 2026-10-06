from . import *


def GetAbilities() -> Sequence['Ability']:

    def defeated_by_attorney(
        effect: 'Effect',
        message: 'Message.AfterUnitDefeatedScheme',
    ) -> bool:
        finder = CardFinder(
            card_type=AlterEgo|Hero|Ally|Support,
            trait="ATTORNEY",
        )
        return finder.Check(message.killer)

    def nelson_and_murdock(
        effect: 'Effect',
        message: 'Message.AfterUnitDefeatedScheme',
    ) -> None:
        Faces.GiveStatus(effect.targets, "Confused", effect)

    return [
        AbilityFactory.AfterUnitDefeatedScheme(
            AbilityType.Response,
            None,
            SchemeSide2,
            nelson_and_murdock,
            conditions=[defeated_by_attorney],
        ).SetTarget(Enemy, canbe_confused=True),
    ]
