from . import *

# * Blindspot


def GetAbilities() -> Sequence['Ability']:

    def blindspot(effect: 'Effect', message: 'Message.AfterUnitThwartEnd') -> None:
        Faces.GiveStatus(effect.targets, "Confused", effect)

    return [
        AbilityFactory.AfterUnitMakeThwart(
            AbilityType.Response,
            "This",
            blindspot,
        ).SetTarget(
            CardFinder(
                card_type=Enemy,
                with_attach=Upgrade,
                canbe_confused=True,
            )
        ),
    ]
