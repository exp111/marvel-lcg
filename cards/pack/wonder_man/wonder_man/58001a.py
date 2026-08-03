from . import *

# * Wonder Man

def GetAbilities() -> Sequence['Ability']:

    def power_recycling(effect: 'Effect', ui: List['CardFace']) -> int:
        ionic = FindIonicPhysiology(effect)
        if ionic:
            ui.append(ionic)
            return ionic.GetPlacedCardArea().GetSize()
        return 0

    def discard_ionic_energy(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        ionic = FindIonicPhysiology(effect)
        if ionic:
            Faces.DiscardAll(ionic.GetPlacedCardArea().GetAll(), effect)

    return [
        AbilityFactory.ThisGainKeyword(
            power_recycling,
            attack=1,
            change_on_event=OnEvent.TuckUnder("Identity"),
        ),
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            "This",
            discard_ionic_energy,
            is_basic_attack=True,
        ),
    ]
