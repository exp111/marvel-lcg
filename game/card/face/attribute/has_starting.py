from . import *


class HasStarting(HasAttribute):
    """A player card that may begin the game in its owner's hand."""

    @override
    def __init__(self, paper: 'Paper') -> None:
        self.printed_starting = 0

        super().__init__(paper)

        self.RegisterAttribute("Starting", "printed_starting")
