from cards.pack import *


def GetRaftScheme(effect: 'Effect') -> 'MainScheme|None':
    face = Worlds.FindCardOnField(
        effect,
        CardFinder(name="The Raft Breakout", card_type=MainScheme),
    )
    return face.CastTo(MainScheme) if face else None


def ActivationBoostCards(
    message: 'Message.AfterUnitAttackEnd',
) -> List['CardFace']:
    cards: List[CardFace] = []
    for attack in message.atk_messages:
        cards.extend(attack.boost_faces)
    return Types.RemoveDuplicates(cards)
