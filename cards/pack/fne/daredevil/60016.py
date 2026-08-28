from . import *


def GetAbilities() -> Sequence['Ability']:

    def sister_maggie(effect: 'Effect', message: 'Message.AfterUnitRecovery') -> None:
        identity = effect.GetInitiator().GetIdentity()
        effect.GetInitiator().AskDiscardFace(
            identity.components.status.GetDeck().Get(),
            effect,
        )

    return [
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            CardFinder(name="Matt Murdock", card_type=AlterEgo),
            recover=3,
        ),
        AbilityFactory.AfterUnitMakeRecovery(
            AbilityType.Response,
            "You",
            sister_maggie,
            conditions=[
                lambda effect, message: effect.GetInitiator().GetIdentity().HasStatus("Any"),
            ],
        ),
    ]
