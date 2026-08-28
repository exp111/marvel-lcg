from . import *


def GetAbilities() -> Sequence['Ability']:
    def is_not_reserved_for_tucked_play(
        effect: 'Effect',
        message: 'Message.CheckPlayerCanPayCost',
    ) -> bool:
        player = message.GetToPlayer()
        if not player.IsHero():
            return True

        identity = player.GetIdentity()
        paying_face = message.paying_for_effect.this
        if paying_face.card.area != identity.GetPlacedCardArea():
            return True

        reflexes = GetPhotographicReflexesInHand(player)
        return not reflexes or effect.this != reflexes[0]

    # Echo's hero side supplies the play permission, cost reduction, and
    # discard. Keep one copy in hand to pay that discard cost; any additional
    # copies may still be spent as resources.
    return [
        AbilityFactory.CheckThisCanDropPay(
            conditions=[is_not_reserved_for_tucked_play],
        ),
    ]
