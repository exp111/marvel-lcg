from cards.pack import *


TRACKSUIT_MINION = CardFinder(trait="TRACKSUIT", card_type=Minion)


def FindTracksuitMafia(effect: 'Effect') -> 'EncounterSideScheme|None':
    return Worlds.FindCardOnField(
        effect,
        name="Tracksuit Mafia",
        card_type=EncounterSideScheme,
    )
