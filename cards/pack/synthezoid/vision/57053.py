from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        upgrades = player.GetControlCardsByType(upgrade=True)
        face = None
        if upgrades:
            face = player.AskChooseFace(upgrades, effect)
        leader = Worlds.GetEnemyLeader(effect)
        forms = leader.GetAttachedAttachments() if leader else []
        dense = CardFinder(name="Dense").Checks(forms)
        intangible = CardFinder(name="Intangible").Checks(forms)
        if face:
            if intangible:
                Faces.DiscardAll([face], effect)
            else:
                Faces.ExhaustAll([face], effect)
        if dense:
            dense[0].card.Flip(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
