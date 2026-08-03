from . import *

# "What Are You?"

def GetAbilities() -> Sequence['Ability']:

    def what_are_you(effect: 'Effect', message: 'Message.WhenUnitWouldBeDefeated') -> None:
        this = effect.this.CastTo(Upgrade)
        identity = effect.GetInitiator().GetIdentity()
        message.SetBeInstead(effect)
        identity.SetHealth(4, effect)
        identity.ChangeToForm(AlterEgo, effect)

        ionic = FindIonicPhysiology(effect)
        if ionic:
            available = [
                face for face in effect.GetInitiator().discard_pile.Get(True)
                if Event.IsType(face) and HasPrintedEnergy(face)
            ]
            room = 3 - ionic.GetPlacedCardArea().GetSize()
            if room > 0 and available:
                effect.GetInitiator().ChooseAbilities(
                    effect,
                    AbilityFactory.ForChoiceAbility(
                        "Tuck up to 3 energy events under Ionic Physiology",
                        lambda targets: ionic.TuckCardUnderHere(targets, effect),
                    ).SetTarget(available, range=(0, min(room, len(available)))),
                )

        Faces.RemoveAllFromGame([this], effect)

    return [
        AbilityFactory.WhenUnitWouldBeDefeated(
            AbilityType.ForcedInterrupt,
            CardFinder(name="Wonder Man"),
            what_are_you,
        ),
    ]

