from cards.pack.wonder_man import *


def FindIonicPhysiology(by_effect: 'Effect') -> 'Upgrade|None':
    face = Worlds.FindCardOnField(
        by_effect,
        name="Ionic Physiology",
        card_type=Upgrade,
        owner=by_effect.GetInitiator(),
    )
    return face.CastTo(Upgrade) if face else None


def HasPrintedEnergy(face: 'CardFace') -> bool:
    return FacesCounter.GetPrintedResources([face]).HasColorPrinted("Y")


def EnergyOverpaid(effect: 'Effect', maximum: int) -> int:
    paid_energy = effect.GetPaidResources(ask_specify_green=True).GetColor(
        "Y",
        convert_green_res=False,
    )
    return min(maximum, effect.GetCostX(), paid_energy)
