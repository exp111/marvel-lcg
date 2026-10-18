from . import *

# Superhero Jailbreak
def GetAbilities() -> Sequence['Ability']:
    def jailbreak(effect: 'Effect', message: 'Message.AfterResolveVillainPhaseStep') -> None:
        discarded_minions: Dict['Player', 'Minion'] = {}

        def discard(player: 'Player') -> None:
            face = Worlds.DiscardEncounterTopCard(effect)
            if face and Minion.IsType(face):
                discarded_minions[player] = face

        def engage(player: 'Player') -> None:
            face = discarded_minions.get(player)
            if face and not face.IsInPlay():
                face.PutIntoPlay(player, effect)

        # Resolve the two printed sentences separately: finish every discard
        # before any minion enters play or triggers its engagement abilities.
        Players.ForEachPlayer(effect, discard)
        Players.ForEachPlayer(effect, engage)

    return [
        AbilityFactory.AfterResolveVillainPhaseStep(AbilityType.ForcedResponse, 1, jailbreak),
    ]
