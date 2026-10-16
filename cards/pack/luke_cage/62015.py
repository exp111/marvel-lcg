from . import *

# Take a Stand
def GetAbilities():
    def stand(effect,message):
        # Keep the bonus through a villain-phase defense until the next player phase ends.
        for ally in effect.GetInitiator().GetControlAllies():
            ally.TemporaryGain(effect,None,end_event=Message.WhenPhaseEnd,
                until_player_phase_end=True,attack=1,thwart=1)
    return [AbilityFactory.AfterUnitDefendAgainstAttack(AbilityType.HeroResponse,"You",stand).SetPlay()]
