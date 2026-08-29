from . import *

# The Best Offense...


def apply_the_best_offense(
    effect: 'Effect',
    face: 'CardFace',
    diff: int,
) -> None:
    buff = face.GetBuff(BuffUseDefenseForAttackAndThwart)
    if diff > 0:
        buff.OnGain(effect)
    elif diff < 0:
        buff.OnLost(effect)


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        *AbilityFactory.GiveKeywordToAttached(
            Hero,
            defense=1,
            apply=apply_the_best_offense,
        ),
    ]
