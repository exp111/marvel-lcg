from . import *


def GetAbilities() -> Sequence['Ability']:
    def maggia_scheme(effect: 'Effect', ui: List['CardFace']) -> Tuple[int, bool]:
        this = effect.this.CastTo(Minion)
        enemies = Worlds.FindCardsOnField(effect, trait="MAGGIA", card_type=Enemy)
        ui.extend(enemies)
        value = len(enemies)
        return value, value != this.scheme

    return [
        AbilityFactory.ThisSetKeyword(
            maggia_scheme,
            scheme=1,
            change_on_event=OnEvent.CardInPlay(MAGGIA_ENEMY),
        ),
    ]
