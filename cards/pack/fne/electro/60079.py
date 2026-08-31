from . import *


def GetAbilities() -> Sequence['Ability']:
    def electro_attacks(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        this = effect.this.CastTo(Attachment)
        if this.GetCounters('charge') <= 0:
            return
        Faces.RemoveCountersOn([this], 1, 'charge', effect)
        message.GiveAdditionalBoostCardForThisActivation(1, effect)
        message.GainOverKill(effect)

    remove_charge = lambda effect, targets: Faces.RemoveCountersOn(
        [effect.this.CastTo(Attachment)], 1, 'charge', effect
    )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(ELECTRO),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            ELECTRO,
            electro_attacks,
            conditions=[
                lambda effect, message:
                    effect.this.CastTo(Attachment).GetCounters('charge') > 0,
            ],
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            lambda effect, message: remove_charge(effect, []),
            conditions=[
                lambda effect, message:
                    effect.this.CastTo(Attachment).GetCounters('charge') > 0,
            ],
        ).SetCost(Cost("Y", or_cost=Cost("2"))).SetName(
            "Spend an energy resource or 2 resources of any type → remove 1 charge counter"
        ).AnyPlayerCanDoThis(),
    ]
