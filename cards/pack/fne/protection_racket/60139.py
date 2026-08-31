from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Ally)
        player = message.GetToPlayer()
        this.card.SetOwner(player)
        this.PutIntoPlay(player, effect, under_control=True)
        ThisCardGainSurge(effect)

    def leaves(effect: 'Effect', message: 'Message.WhenCardLeavePlay') -> None:
        player = message.trigger.GetControlBy()
        if not isinstance(player, Player):
            player = message.trigger.card.GetOwner()
        if isinstance(player, Player):
            scheme = GetProtectionRacketScheme(player, effect)
            if scheme:
                scheme.PlaceThreatOnSchemes([scheme], 4, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardLeavePlay(
            AbilityType.ForcedInterrupt,
            "This",
            leaves,
        ),
    ]
