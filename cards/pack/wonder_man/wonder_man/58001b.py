from . import *

# * Simon Williams

def GetAbilities() -> Sequence['Ability']:

    def simon_williams(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        initiator = effect.GetInitiator()
        face = Search.PlayerCard(
            effect,
            initiator,
            include_player_deck=True,
            include_discard_pile=True,
            name="Ionic Physiology",
            card_type=Upgrade,
        )
        if face:
            face.PutIntoPlay(initiator, effect)

    return [
        AbilityFactory.WhenCardSetup(
            "This",
            simon_williams,
        ).SetName("Ionic Energy Being"),
    ]

