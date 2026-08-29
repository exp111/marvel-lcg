from cards.pack import *


VEHICLE_ATTACHMENT = CardFinder(trait="VEHICLE", card_type=Attachment)


def HasVehicleAttachment(face: 'CardFace') -> bool:
    return bool(VEHICLE_ATTACHMENT.Checks(face.GetAttachedAttachments()))


def VehicleAttachmentAbilities(
    damage_threshold: int,
    **target_order: Any,
) -> List['Ability']:
    def no_vehicle(effect: 'Effect', enemy: 'Enemy') -> bool:
        Unused(effect)
        return not HasVehicleAttachment(enemy)

    def absorb_damage(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        message.SetBeInstead(effect)
        Faces.PlaceCountersOn(
            [this],
            message.will_take_damage,
            "damage",
            effect,
        )
        if this.GetCounters("damage") >= damage_threshold:
            Faces.DiscardAll([this], effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(
                card_type=Enemy,
                check_effect_fn=no_vehicle,
            ),
            if_cannot_gain_surge=True,
            **target_order,
        ),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            absorb_damage,
        ),
    ]
