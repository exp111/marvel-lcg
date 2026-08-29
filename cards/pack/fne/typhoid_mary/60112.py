from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        villains = Worlds.GetSetAsideAreaCards(effect, TYPHOID_VILLAIN)
        if not villains:
            return
        villain = villains[0]
        if Rand.RandomChoice([False, True], effect):
            villain.card.Flip(effect, call_reveal=False)
            villain = villain.card.face
        villain.PutIntoPlay(Worlds.GetFirstPlayer(effect), effect)

    def villain_phase_end(effect: 'Effect', message: 'Message.WhenPhaseEnd') -> None:
        villain = GetTyphoidVillain(effect)
        if villain:
            villain.card.Flip(effect)

    def counter_placed(effect: 'Effect', message: 'Message.AfterCardPlacedCounter') -> None:
        psyche = effect.this.CastTo(Environment)
        if psyche.GetAllCounters() >= 3:
            Worlds.SetGameOver(True, effect)

    return [
        AbilityFactory.WhenCardSetup("This", setup),
        AbilityFactory.WhenVillainPhaseEnd(
            AbilityType.ForcedInterrupt,
            villain_phase_end,
        ),
        AbilityFactory.AfterCounterPlacedOn(
            AbilityType.ForcedResponse,
            "This",
            None,
            counter_placed,
        ),
    ]
