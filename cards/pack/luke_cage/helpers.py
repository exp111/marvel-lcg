from . import *


def UnbreakableSkin():
    return [
        # Both printed forms allow multiple Tough cards. The Colossus helper
        # removes excess cards when its face becomes inactive, which would
        # incorrectly discard Luke's Tough cards during the form-change gap.
        Ability(AbilityType.NonKeyword, Message.GettingUnitAdditionalTough,
            [lambda effect, message: Condition.CheckWhichCard("This", message.trigger, effect)],
            lambda effect, message: message.SetReturn(effect.this.CastTo(Unit2).tough), is_local=True),
        AbilityFactory.UnitAttackGainKeyword(None, "This", lost_piercing=True),
    ]
