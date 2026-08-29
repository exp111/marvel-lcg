from . import *


def GetAbilities() -> Sequence['Ability']:

    def living_lie_detector(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        target = effect.targets[0]
        attached_upgrades = len(target.GetAttachedUpgrades())
        bonus = 0
        if attached_upgrades:
            bonus = effect.GetInitiator().AskChooseOneText(
                list(range(attached_upgrades + 1)),
                [
                    f"Remove {value} additional threat"
                    for value in range(attached_upgrades + 1)
                ],
            )
        threat = 2 + bonus
        effect.this.CastTo(Event).RemoveThreatFromSchemes([target], threat, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            living_lie_detector,
        ).SetPlay().SetLabel("thwart").SetTarget(Scheme2),
    ]
