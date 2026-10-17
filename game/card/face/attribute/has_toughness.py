from . import *

class HasToughness(HasAttribute):
    @override
    def __init__(self, paper: 'Paper') -> None:
        self.printed_toughness: int = 0

        super().__init__(paper)

        self.RegisterAttribute("Toughness", "printed_toughness")
        self.RegisterInfoDict('toughness')

    @override
    def GetAbilities(self) -> List['Ability']:
        def give_tough(
            effect: 'Effect',
            message: 'Message.AfterCardEnterPlay|Message.AfterCardFaceActivated',
        ) -> None:
            from game.effect.rule import Toughness
            from game.operate.faces import Faces

            Faces.GiveStatus([effect.this], "Tough", Toughness(effect.this))

        return [
            Ability(
                AbilityType.ForcedResponse,
                # Newly exposed characters (e.g. Strong Inhuman, Black Swan,
                # and the next Apocalypse stage) still initialize Toughness.
                # This must not broadcast an entry to other cards' responses.
                Message.AfterCardEnterPlay|Message.AfterCardFaceActivated,
                [
                    lambda effect, message:
                        bool(effect.world.rule.v18_timing) and
                        effect.this is message.trigger and
                        effect.this.CastTo(HasToughness).IsToughness() and
                        effect.this.IsInPlay()
                ],
                give_tough,
                is_local=True,
            ).SetName("Toughness")
        ] + super().GetAbilities()

    @override
    def OnWhenCardEnterPlay(self, message: 'Message.WhenCardEnterPlay') -> bool:
        from game.effect.rule import Toughness
        from game.operate.faces import Faces
        if super().OnWhenCardEnterPlay(message):
            if self.IsToughness() and not bool(self.card.world.rule.v18_timing):
                Faces.GiveStatus([self], "Tough", Toughness(self))
            return True
        return False

    @override
    def OnWhenCardFaceActivated(self, message: 'Message.WhenCardFaceActivated') -> bool:
        from game.effect.rule import Toughness
        from game.operate.faces import Faces
        if super().OnWhenCardFaceActivated(message):
            if self.IsToughness() and not bool(self.card.world.rule.v18_timing):
                Faces.GiveStatus([self], "Tough", Toughness(self))
            return True
        return False

    ################################################################################
    #
    @override
    def OnResetKeywords(self, by_effect: 'Effect'):
        self.GainToughness(self.printed_toughness, by_effect)
        return super().OnResetKeywords(by_effect)

    @final
    def IsToughness(self) -> bool:
        return self.toughness > 0

    @final
    @property
    def toughness(self) -> int:
        return self.GetKeyword('Toughness')

    @final
    def GainToughness(self, diff: int, by_effect: 'Effect'):
        self.GainKeyword(diff, 'Toughness', by_effect)

