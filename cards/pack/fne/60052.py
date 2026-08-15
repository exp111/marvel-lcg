from . import *

# The Best Offense...


def GetAbilities() -> Sequence['Ability']:

    def the_best_offense(effect: 'Effect', message: 'Message.WhenUnitUseBasicPower') -> None:
        hero = message.trigger.CastTo(Hero)
        if message.power == "ATK":
            message.GainValue(hero.defense - hero.attack, effect)
        elif message.power == "THW":
            message.GainValue(hero.defense - hero.thwart, effect)

    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        *AbilityFactory.GiveKeywordToAttached(
            Hero,
            defense=1,
        ),
        AbilityFactory.WhenUnitUseBasicPower(
            AbilityType.NonKeyword,
            "You",
            the_best_offense,
            powers=["ATK", "THW"],
        ),
    ]
