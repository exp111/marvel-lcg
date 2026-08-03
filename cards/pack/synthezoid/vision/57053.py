from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        upgrades = player.GetControlCardsByType(upgrade=True)
        if upgrades:
            face = player.AskChooseFace(upgrades, effect)
            if face:
                Faces.ExhaustAll([face], effect)
        leader = Worlds.GetEnemyLeader(effect)
        if leader and CardFinder(name="Dense").Checks(leader.GetAttachedAttachments()):
            leader.GetAttachedAttachments()[0].card.Flip(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
