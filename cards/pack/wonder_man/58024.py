from . import *

# * Jarvis

def GetAbilities() -> Sequence['Ability']:

    def jarvis(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> None:
        identity = message.trigger.CastTo(Identity)
        player = effect.GetInitiator()

        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "That identity gets +2 REC until the end of the phase",
                lambda targets: identity.GainUntilPhaseEnd(effect, recover=2),
            ),
            AbilityFactory.ForChoiceAbility(
                "Discard a status card from that identity",
                lambda targets: Faces.DiscardAll(targets, effect),
            ).SetTarget(identity.components.status.GetDeck().GetAll()),
        )

    return [
        AbilityFactory.AfterUnitChangeForm(
            AbilityType.Response,
            None,
            jarvis,
            to_form=AlterEgo,
            conditions=[
                lambda effect, message:
                    message.would_change_message.from_form.HasTrait("AVENGER"),
            ],
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]
