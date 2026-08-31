from . import *


def GetAbilities() -> Sequence['Ability']:
    def carjacking(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()
        identity = player.GetIdentity()
        vehicle = Worlds.DiscardEncounterCardsUntil(
            effect,
            trait="VEHICLE",
            card_type=Attachment,
        )
        if not vehicle:
            return

        def reveal_vehicle(targets: Sequence['CardFace']) -> None:
            Unused(targets)
            vehicle.Reveal(player, effect)

        if HasVehicleAttachment(identity):
            reveal_vehicle([])
            return

        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbilityWithCost(
                Cost("3", same_type=True),
                "Spend 3 resources of the same type → attach the VEHICLE to your identity",
                lambda targets, resources: vehicle.AttachTo2(identity, effect),
            ),
            AbilityFactory.ForChoiceAbility(
                "Reveal the discarded VEHICLE attachment",
                reveal_vehicle,
            ),
        )

    return [AbilityFactory.WhenThisRevealed(None, carjacking)]
