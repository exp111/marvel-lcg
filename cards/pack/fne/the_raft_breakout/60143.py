from . import *


def GetAbilities() -> Sequence['Ability']:
    def villain_schemed(
        effect: 'Effect',
        message: 'Message.AfterUnitSchemeEnd',
    ) -> None:
        player = message.GetAgainstPlayer()
        if not player:
            return
        for boost in message.boost_cards:
            if Minion.IsType(boost):
                player.DealEncounterCard(boost, effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(Villain),
        AbilityFactory.AfterUnitSchemeEnd(
            AbilityType.ForcedResponse,
            "AttachedCharacter",
            villain_schemed,
        ),
    ]
