from . import *

# "Big Mistake"
from .helpers import Alias

def GetAbilities():
    def big_mistake(effect, message):
        alias = Alias(effect)
        player = effect.GetInitiator()
        damage, properties = 3, AttackProperty()
        if alias and alias.GetCounters("evidence") and player.MayChooseOneText(["Remove 1 evidence for +2 damage and overkill or piercing"]):
            if alias.RemoveCountersInternal(1, "evidence", effect, forced=False):
                damage = 5
                player.ChooseAbilities(effect,
                    AbilityFactory.ForChoiceAbility("Overkill", lambda targets: setattr(properties, "overkill", True)),
                    AbilityFactory.ForChoiceAbility("Piercing", lambda targets: setattr(properties, "piercing", True)))
        effect.this.DealDamage(effect.targets, damage, effect, property=properties)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction, big_mistake)
            .SetPlay().SetLabel("attack").SetTarget(Enemy)]
