from . import *


def GetAbilities() -> Sequence['Ability']:
    def chameleon_scheme(effect: 'Effect', ui: List['CardFace']) -> Tuple[int, bool]:
        this = effect.this.CastTo(Minion)
        characters = Worlds.GetOnFieldFriendlyCharacters(effect)
        character = Filter.One(characters, effect, highest_thw=True)
        value = 1 + (
            character.thwart if character and HasThwart.IsType(character) else 0
        )
        if character:
            ui.append(character)
        return value, value != this.scheme

    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        effect.this.CastTo(Minion).DoSchemes(message.GetToPlayer(), effect)

    return [
        AbilityFactory.ThisSetKeyword(
            chameleon_scheme,
            scheme=1,
            change_on_event=OnEvent.CardKeyword("Character"),
        ),
        AbilityFactory.WhenThisRevealed(None, revealed),
    ]
