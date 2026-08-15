from . import *

class HasSurge(HasAttribute):

    @override
    def __init__(self, paper: 'Paper') -> None:
        self.printed_surge = 0

        super().__init__(paper)

        self.RegisterAttribute("Surge", "printed_surge")
        self.RegisterInfoDict('surge')

    @override
    def OnResetKeywords(self, by_effect: 'Effect'):
        self.GainSurge(self.printed_surge, by_effect)
        return super().OnResetKeywords(by_effect)

    @final
    def GainSurge(self, diff: int, by_effect: 'Effect'):
        self.GainKeyword(diff, 'Surge', by_effect)

    @final
    @property
    def surge(self) -> int:
        return self.GetKeyword('Surge')

class CanSurge(HasSurge):

    @final
    def ResolveSurge(self, player: 'Player') -> 'Effect|None':
        if not self.surge:
            return None

        from game.message import Message
        from game.effect.rule import Surge
        surge_message = Message.WhenSurgeWouldBeResolved(self, player)
        surge_message.Send()
        if not surge_message.is_be_instead:
            effect = Surge(self)

            world = self.card.world
            if world.rule.fix_surge:
                # Rules Reference v1.8 defines surge as a When Revealed
                # ability that deals a facedown encounter card. A normal deal
                # puts that card at the end of the player's encounter-card
                # queue, so it waits for step four of the villain phase when
                # surge resolves outside that step.
                player.DealEncounterCards(1, effect, to_end_of_queue=True)
            else:
                player.DealEncounterCards(1, effect, by_surge=True)
            return effect
        return None
