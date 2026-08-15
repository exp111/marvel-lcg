from . import *

# Legal Trouble


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.ReduceCostToPlayFaceWhen(
            "This",
            1,
            "You",
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().GetIdentity().HasTrait("ATTORNEY", "POLICE")
            ],
        ),
        AbilityFactory.CanPlayThisUpgradeCard(Minion),
        *AbilityFactory.GiveKeywordToAttached(
            Minion,
            scheme=-2,
        ),
    ]
