from . import *


def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenUnitBeDefeated') -> None:
        cards = [
            face
            for player in Worlds.GetPlayers(effect)
            for face in player.GetControlCards()
            if Support.IsType(face) or Upgrade.IsType(face)
        ]
        face = Filter.One(cards, effect, highest_cost=True)
        if face:
            Faces.DiscardAll([face], effect)

    return [
        AbilityFactory.UnitAttackGainKeyword("This", piercing=True),
        InfluencedMinionDefeated(defeated),
    ]
