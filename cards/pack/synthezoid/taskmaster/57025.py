from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        def otherwise() -> None:
            leader = Worlds.GetEnemyLeader(effect)
            if leader:
                Faces.GiveStatus([leader], "Tough", effect)
                Faces.GiveFacedownBoostCards([leader], 1, effect)

        taskmasters = Worlds.GetOnFieldEnemies(
            effect, CardFinder(name="Taskmaster", card_type=Minion)
        )
        if taskmasters and Worlds.GetYourTeamLeader(effect):
            taskmasters[0].DoAttackYou(
                "YourLeader", effect, if_no_attack_was_made=otherwise
            )
        else:
            otherwise()

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        message.GiveActivatingEnemyAdditionalBoostCard(1, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
