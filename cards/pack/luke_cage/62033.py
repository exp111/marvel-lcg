from . import *

# Sidewinder
def GetAbilities():
    def sidewinder(effect,message):
        top=Worlds.DiscardEncounterTopCard(effect)
        if top and HasBoostIcon.IsType(top) and top.CastTo(HasBoostIcon).boost_star:
            player=message.attacker.GetControlByPlayer()
            player.DealEncounterCard(effect.this,effect)
    return [AbilityFactory.WhenUnitBeingAttack(AbilityType.ForcedInterrupt,"This",None,sidewinder)]
