from . import *


def GetAbilities() -> Sequence['Ability']:
    def would_take_damage(effect: 'Effect', message: 'Message.WhenUnitWouldTakeDamage') -> None:
        this = effect.this.CastTo(Attachment)
        damage = message.will_take_damage
        message.PreventDamage(damage, effect)
        Faces.PlaceCountersOn([this], damage, 'damage', effect)
        threshold = 8 if Worlds.IsExpert(effect) else 5
        if this.GetCounters('damage') >= threshold:
            Faces.DiscardAll([this], effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        Faces.GiveStatus([message.GetToPlayer().GetIdentity()], "Confused", effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(TYPHOID_VILLAIN),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "AttachedEnemy",
            would_take_damage,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Bloody Mary"),
        ),
    ]
