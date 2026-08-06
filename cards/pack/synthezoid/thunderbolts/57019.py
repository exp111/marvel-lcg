from . import *

def GetAbilities() -> Sequence['Ability']:
    def damage(effect: 'Effect', message: 'Message.WhenCardRevealed|Message.WhenCardBecomeBoost') -> None:
        leader = Worlds.GetYourTeamLeader(effect)
        if leader:
            effect.this.DealDamage([leader], 2, effect)
            return

        player = message.GetToPlayer()
        target = player.AskChooseFace(player.GetControlCharacters(), effect)
        if target:
            amount = 2 if isinstance(message, Message.WhenCardRevealed) else 1
            effect.this.DealDamage([target], amount, effect)
    return [
        AbilityFactory.WhenThisRevealed(None, damage),
        AbilityFactory.WhenCardBecomeBoost("This", damage),
    ]
