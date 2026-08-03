from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        leader = Worlds.GetEnemyLeader(effect)
        if not leader:
            return
        forms = leader.GetAttachedAttachments()
        if player.IsAlterEgo():
            value = 1 if CardFinder(name="Intangible").Checks(forms) else 0
            leader.DoSchemes(player, effect, property=SchemeProperty(additional_value=value))
        else:
            value = 1 if CardFinder(name="Dense").Checks(forms) else 0
            leader.DoAttackYou(player, effect, property=AttackProperty(additional_value=value))
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
