from . import *


def GetAbilities() -> Sequence['Ability']:

    def defeated_by_your_attorney(
        effect: 'Effect',
        message: 'Message.WhenSchemeBeDefeated',
    ) -> bool:
        finder = CardFinder(
            card_type=AlterEgo|Hero|Ally|Support,
            trait="ATTORNEY",
        )
        return finder.Check(message.killer)

    def nelson_and_murdock(
        effect: 'Effect',
        message: 'Message.WhenSchemeBeDefeated',
    ) -> None:
        Faces.GiveStatus(effect.targets, "Confused", effect)

    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.Response,
            SchemeSide2,
            nelson_and_murdock,
            has_defeating_player=True,
            conditions=[defeated_by_your_attorney],
        ).SetTarget(Enemy, canbe_confused=True),
    ]
