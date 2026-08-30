from . import *

class HasRestricted(HasAttribute):
    @override
    def __init__(self, paper: 'Paper') -> None:
        self.printed_restricted = 0

        super().__init__(paper)

        self.RegisterAttribute("Restricted", "printed_restricted")
        self.RegisterInfoDict('restricted')

    @override
    def GetAbilities(self) -> List['Ability']:
        def after_take_control(
            effect: 'Effect',
            message: 'Message.AfterCardEnterPlay|Message.AfterCardControlChanged',
        ) -> bool:
            if not bool(effect.world.rule.v18_timing) or \
                effect.this is not message.trigger or \
                effect.this.CastTo(HasRestricted).restricted <= 0 or \
                not effect.this.IsInPlay():
                return False
            if isinstance(message, Message.AfterCardControlChanged):
                return Player.IsType(message.to_controller)
            return True

        return [
            Ability(
                AbilityType.ForcedResponse,
                Message.AfterCardEnterPlay|Message.AfterCardControlChanged,
                [after_take_control],
                lambda effect, message:
                    effect.this.CastTo(HasRestricted).CheckRestrictedLimit([]),
                is_local=True,
            ).SetName("Restricted")
        ] + super().GetAbilities()

    ################################################################################
    #
    def CheckRestrictedLimit(self, gain_faces: List['CardFace']) -> bool:
        player = self.GetControlByPlayer()
        return player.limit_restricted.CheckLimit(gain_faces)

    @override
    def OnNotTreatAsIfBlank(self, message: 'Message.WhenCardTreatAsIfBlank') -> None:
        if self.restricted:
            self.CheckRestrictedLimit([])
        return super().OnNotTreatAsIfBlank(message)

    @override
    def OnWouldEnterPlay(self, into_area: 'Deck') -> bool:
        if super().OnWouldEnterPlay(into_area):
            if self.restricted and not bool(self.card.world.rule.v18_timing):
                if not self.CheckRestrictedLimit([self]):
                    return False
            return True
        return False

    @override
    def OnAfterCardLeavePlay(self, message: 'Message.AfterCardLeavePlay') -> None:
        player = message.from_area.GetOwner()
        if Player.IsType(player):
            player.limit_restricted.CheckLimit([])
        return super().OnAfterCardLeavePlay(message)

    @override
    def OnAfterCardFlip(self, message: 'Message.AfterCardFlip'):
        face = message.to_face
        if face and HasRestricted.IsType(face):
            if face.restricted:
                self.CheckRestrictedLimit([])
        super().OnAfterCardFlip(message)

    ################################################################################
    #
    @override
    def OnResetKeywords(self, by_effect: 'Effect'):
        self.GainRestricted(self.printed_restricted, by_effect)
        return super().OnResetKeywords(by_effect)

    @final
    def GainRestricted(self, diff: int, by_effect: 'Effect'):
        self.GainKeyword(diff, 'Restricted', by_effect)
        if diff > 0:
            self.CheckRestrictedLimit([])

    @final
    @property
    def restricted(self) -> int:
        return self.GetKeyword('Restricted')

