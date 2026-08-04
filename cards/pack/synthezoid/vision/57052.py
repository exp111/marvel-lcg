from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        target = player.AskChooseFace(player.GetControlCharacters(CardFinder(canbe_exhaust=True)), effect)
        if target:
            Faces.ExhaustAll([target], effect)
        leader = Worlds.GetEnemyLeader(effect)
        if not leader:
            return
        forms = leader.GetAttachedAttachments()
        dense = CardFinder(name="Dense").Checks(forms)
        intangible = CardFinder(name="Intangible").Checks(forms)
        if target and dense:
            effect.this.DealDamage([target], 2, effect)
        elif intangible:
            intangible[0].card.Flip(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
