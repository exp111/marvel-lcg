from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        player = message.defeating_player
        if player:
            SetupCards.DealAsFacedownEncounterCard(
                effect, player, name="Blood Debt", card_type=Obligation
            )
    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated, "This", defeated, has_defeating_player=True
        )
    ]
