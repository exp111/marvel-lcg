from . import *

# * Ronin


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            Hero,
            control_by="You",
            condition=lambda effect:
                len(effect.GetInitiator().GetControlAllies()) == 0,
            defense=1,
            retaliate=1,
            change_on_event=OnEvent.CardInPlay(Ally),
        ),
    ]
