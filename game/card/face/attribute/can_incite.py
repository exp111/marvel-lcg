from . import *

class HasIncite(HasAttribute):
    @override
    def __init__(self, paper: 'Paper') -> None:
        """
        When a card with the incite X keyword is revealed, place X threat on the main scheme. (X is the value next to the incite keyword.)
        """
        self.printed_incite = 0

        super().__init__(paper)

        self.RegisterAttribute("Incite", "printed_incite")
        self.RegisterInfoDict('incite')

    @override
    def OnResetKeywords(self, by_effect: 'Effect'):
        self.GainIncite(self.printed_incite, by_effect)
        return super().OnResetKeywords(by_effect)

    @final
    def GainIncite(self, diff: int, by_effect: 'Effect'):
        self.GainKeyword(diff, 'Incite', by_effect)

    @final
    @property
    def incite(self) -> int:
        return self.GetKeyword('Incite')

class CanIncite(HasIncite):

    @override
    def GetAbilities(self) -> List['Ability']:
        def resolve_incite(
            effect: 'Effect',
            message: 'Message.WhenCardRevealed',
        ) -> None:
            this = effect.this.CastTo(CanIncite)
            resolved = this.ResolveIncite()
            if resolved:
                message.reveal_message.AddResolved(resolved)

        ability = Ability(
            AbilityType.WhenRevealed,
            Message.WhenCardRevealed,
            [
                lambda effect, message:
                    bool(effect.world.rule.v18_timing) and
                    effect.this is message.trigger and
                    effect.this.CastTo(CanIncite).incite > 0
            ],
            resolve_incite,
            is_local=True,
        ).SetName("Incite")
        ability.v18_timing_keyword = True
        return [ability] + super().GetAbilities()

    @final
    def ResolveIncite(self) -> 'Effect|None':
        from game.operate.worlds import Worlds

        # When a card with the incite X keyword is revealed,
        # place X threat on the main scheme.
        # (X is the value next to the incite keyword.)
        # Place 1 threat on the main scheme when this card is revealed.
        if not self.incite:
            return None
        from game.effect.rule import Incite
        scheme = Worlds.FindMainScheme(self)
        if scheme:
            effect = Incite(self)
            scheme.PlaceThreatInternal(self.incite, effect)
            return effect
        return None

