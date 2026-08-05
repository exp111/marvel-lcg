from . import *


def GetAbilities() -> Sequence['Ability']:

    def protect_humanity_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Find.FindAndPutIntoPlay(
            effect,
            message.GetToPlayer(),
            name="Amadeus Cho",
            card_type=Ally,
        )

    def redirect_villain(effect: 'Effect', message: 'Message.WhenUnitWouldAttackUnit') -> None:
        this = effect.this.CastTo(Obligation)
        ally = effect.targets[0]
        assert Unit2.IsType(ally)
        message.ChangeTarget(ally, effect)

        attack_message = message.would_atk_message

        def after_attack() -> None:
            defender = attack_message.defender
            if defender and defender.IsName("Hercules", check_all_face=True):
                this.RemoveCountersInternal(1, "labor", effect, forced=True)

        RunAt.AfterEventEnd(effect, attack_message, after_attack)

    def you_control_an_ally(effect: 'Effect', message: 'Message.WhenUnitWouldAttackUnit') -> bool:
        this = effect.this.CastTo(Obligation)
        return bool(this.GetGaveToPlayer().GetControlAllies())

    return [
        AbilityFactory.WhenThisRevealed(None, protect_humanity_revealed),
        AbilityFactory.WhenUnitWouldAttackUnit(
            AbilityType.ForcedInterrupt,
            Villain,
            CardFinder(name="Hercules", card_type=Hero),
            redirect_villain,
            conditions=[you_control_an_ally],
        ).SetTarget(Ally, from_where=["YouControlCards"]),
    ]
