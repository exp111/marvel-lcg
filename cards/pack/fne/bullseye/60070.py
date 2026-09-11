from . import *

# Deadly Sai


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(BULLSEYE),
        AbilityFactory.UnitAttackGainKeyword(
            BULLSEYE,
            piercing=True,
            lost_ranged=True,
        ),
        AbilityFactory.AfterUnitDefendAgainstAttack(
            AbilityType.HeroResponse,
            "YourHero",
            DiscardThisCard,
            attacker=BULLSEYE,
        ).SetCost(Cost("2", different_type=True)),
    ]
