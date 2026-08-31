from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        for player in Worlds.GetPlayers(effect):
            identity = player.GetIdentity()
            if Worlds.IsExpert(effect):
                Faces.GiveStatus([identity], "Stunned", effect)
                Faces.GiveStatus([identity], "Confused", effect)
                continue
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    "Stun your identity",
                    lambda targets, identity=identity:
                        Faces.GiveStatus([identity], "Stunned", effect),
                ),
                AbilityFactory.ForChoiceAbility(
                    "Confuse your identity",
                    lambda targets, identity=identity:
                        Faces.GiveStatus([identity], "Confused", effect),
                ),
            )

    return [CampaignEnvironmentSetup(setup)]
