from . import *


def GetAbilities() -> Sequence['Ability']:
    def enough_thwart(
        effect: 'Effect',
        faces: Sequence['CardFace'],
    ) -> bool:
        Unused(effect)
        return sum(getattr(face, "thwart", 0) for face in faces) >= 3

    exhaust_characters = Select.From(
        "YouControlUnit",
        range=(1, "All"),
        check_again_fn=enough_thwart,
    )

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        effect.this.Reveal(message.GetToPlayer(), effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay("YourIdentity"),
        AbilityFactory.PlayersCannotThwartWhile(
            "AttachedPlayer",
            Scheme2,
        ),
        AbilityFactory.PlayersCannotAttackWhile(
            "AttachedPlayer",
            Enemy,
        ),
        AbilityFactory.PlayersCannotChangeForms(
            AbilityType.NonKeyword,
            "AttachedPlayer",
            from_form=Hero,
            to_form=AlterEgo,
        ),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.HeroAction,
        ).SetCost(Cost("3")).SetName(
            "Spend 3 resources of any type → discard Imprisoned"
        ),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.HeroAction,
        ).SetCostFunc(CostFunc.Exhaust(exhaust_characters)).SetName(
            "Exhaust characters with total THW 3 or more → discard Imprisoned"
        ),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
