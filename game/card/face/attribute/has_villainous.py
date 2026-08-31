from . import *

class HasVillainous(HasAttribute, CanBoost):
    @override
    def __init__(self, paper: 'Paper') -> None:
        self.printed_villainous = 0

        super().__init__(paper)

        self.RegisterAttribute("Villainous", "printed_villainous")
        self.RegisterInfoDict('villainous')

    @override
    def GetAbilities(self) -> List['Ability']:
        def give_boost_card(
            effect: 'Effect',
            message: 'Message.WhenUnitUseBasicPower',
        ) -> None:
            this = effect.this.CastTo(HasVillainous)
            this.GiveFacedownBoostCardsInternal(
                1,
                effect,
                message.would_message,
            )

        return [
            Ability(
                AbilityType.ForcedInterrupt,
                Message.WhenUnitUseBasicPower,
                [
                    lambda effect, message:
                        bool(effect.world.rule.v18_timing) and
                        effect.this is message.trigger and
                        effect.this.CastTo(HasVillainous).IsVillainous()
                ],
                give_boost_card,
                is_local=True,
            ).SetName("Villainous")
        ] + super().GetAbilities()

    @override
    def GetBoostCardNum(self, message: 'Message2') -> int:
        if bool(self.card.world.rule.v18_timing):
            return 0
        return 1 if self.IsVillainous() else 0

    ################################################################################
    #
    @override
    def OnResetKeywords(self, by_effect: 'Effect'):
        self.GainVillainous(self.printed_villainous, by_effect)
        return super().OnResetKeywords(by_effect)

    @final
    def IsVillainous(self) -> bool:
        return self.villainous > 0

    @final
    @property
    def villainous(self) -> int:
        return self.GetKeyword('Villainous')

    @final
    def GainVillainous(self, diff: int, by_effect: 'Effect'):
        self.GainKeyword(diff, 'Villainous', by_effect)

