from . import *


def GetAbilities() -> Sequence['Ability']:
    def placing_character(
        message: 'Message.WhenSchemeWouldPlaceThreat',
    ) -> 'CardFace|None':
        if message.sch_message:
            return message.sch_message.trigger
        return message.by_effect.this if Unit2.IsType(message.by_effect.this) else None

    def vehicle_places_threat(
        effect: 'Effect',
        message: 'Message.WhenSchemeWouldPlaceThreat',
    ) -> bool:
        character = placing_character(message)
        return bool(
            message.trigger != effect.this
            and character
            and HasVehicleAttachment(character)
        )

    def vehicle_removes_threat(
        effect: 'Effect',
        message: 'Message.WhenSchemeWouldRemoveThreat',
    ) -> bool:
        return bool(
            message.trigger != effect.this
            and Unit2.IsType(message.by_face)
            and HasVehicleAttachment(message.by_face)
        )

    def redirect_placed_threat(
        effect: 'Effect',
        message: 'Message.WhenSchemeWouldPlaceThreat',
    ) -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        message.SetBeInstead(effect)
        this.PlaceThreatOnSchemes([this], message.value, effect)

    def redirect_removed_threat(
        effect: 'Effect',
        message: 'Message.WhenSchemeWouldRemoveThreat',
    ) -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        message.SetBeInstead(effect)
        this.RemoveThreatFromSchemes([this], message.value, effect)

    return [
        AbilityFactory.WhenSchemeWouldPlaceThreat(
            AbilityType.ForcedInterrupt,
            None,
            redirect_placed_threat,
            conditions=[vehicle_places_threat],
        ),
        AbilityFactory.WhenSchemeWouldRemoveThreat(
            AbilityType.ForcedInterrupt,
            None,
            redirect_removed_threat,
            conditions=[vehicle_removes_threat],
        ),
    ]
