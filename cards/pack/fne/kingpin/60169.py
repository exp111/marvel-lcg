from . import *


def GetAbilities() -> Sequence['Ability']:
    def place_threat_and_take_control(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Minion)
        Faces.PlaceCountersOn([this], 1, "threat", effect, maximum=4)
        if this.GetCounters("threat") == 4:
            Faces.TreatAsAlly(
                this,
                "kingpin_black_cat_ally",
                effect.GetInitiator(),
                effect,
            )

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            place_threat_and_take_control,
            conditions=[
                lambda effect, message:
                    effect.this.GetCounters("threat") < 4,
            ],
        ).SetCost(Cost("B")).SetName(
            "Spend a mental resource → place 1 threat here"
        ).AnyPlayerCanDoThis(),
    ]
