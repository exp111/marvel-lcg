from . import *


def GetAbilities() -> Sequence['Ability']:
    def process(minion: 'Minion', ally: 'Ally', effect: 'Effect') -> None:
        Unused(ally)
        minion.GainTraits(1, ["INFLUENCED"], effect)

    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Attachment)
        ally = Filter.One(message.GetToPlayer().GetControlAllies(), effect, highest_cost=True)
        if ally:
            this.AttachTo2(ally, effect)
        else:
            this.GainSurge(1, effect)

    return [
        AbilityFactory.TreatAttachedCardAsMinion(Ally, "Minion", process=process),
        AbilityFactory.WhenThisRevealed(None, revealed),
    ]
