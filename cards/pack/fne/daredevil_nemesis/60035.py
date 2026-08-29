from . import *


def GetAbilities() -> Sequence['Ability']:

    def stolen_sai_action(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        this = effect.this.CastTo(Attachment)
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Attach Stolen Sai to Elektra",
                lambda targets: this.AttachTo2(targets[0], effect),
            ).SetTarget(CardFinder(name="Elektra", card_type=Ally)),
            AbilityFactory.ForChoiceAbility(
                "Discard Stolen Sai",
                lambda targets: Faces.DiscardAll([this], effect),
            ).SetHasNoTargetEffect(),
        )

    def stolen_sai_boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        message.would_atk_message.GainPiercing(effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            Enemy,
            highest_atk=True,
        ),
        AbilityFactory.UnitAttackGainKeyword(
            "AttachedCharacter",
            piercing=True,
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            stolen_sai_action,
        ).SetCost(Cost("RR")),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            stolen_sai_boost,
            during_attack=True,
        ),
    ]
