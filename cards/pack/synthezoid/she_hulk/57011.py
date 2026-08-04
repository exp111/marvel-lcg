from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        faces = [*player.GetControlCardsByType(ally=True), *player.GetControlCardsByType(support=True)]
        face = Filter.One(faces, effect, highest_cost=True)
        if face and HasCost.IsType(face):
            value = face.printed_cost.val
            Faces.DiscardAll([face], effect)
            if not this.PlaceThreatOnSchemes("MainScheme", value, effect):
                ThisCardGainSurge(effect)
        else:
            ThisCardGainSurge(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
