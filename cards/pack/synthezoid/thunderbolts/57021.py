from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.PlayersCannotRemoveThreatFrom(
            "AnyPlayer",
            "This",
            conditions=[lambda effect, message: bool(Worlds.GetOnFieldEnemies(
                effect, CardFinder(card_type=Minion, trait="THUNDERBOLT")
            ))],
        )
    ]
