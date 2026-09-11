from cards.pack.fne import *


def YourIdentityWouldRemoveLastThreat(
    effect: 'Effect',
    message: 'Message.WhenSchemeWouldRemoveThreat',
) -> bool:
    return (
        not message.is_be_instead
        and not message.cannot_be_removed
        and 0 < message.trigger.CastTo(Scheme2).threat <= message.value
        and Condition.CheckWhichCard("YourIdentity", message.by_face, effect)
    )
