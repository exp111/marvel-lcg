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
        if CardFinder(name="Dense").Checks(forms):
            effect.this.DealDamage([player.GetIdentity()], 2, effect)
        elif CardFinder(name="Intangible").Checks(forms):
            forms[0].card.Flip(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
