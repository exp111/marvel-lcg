from core import *

@dataclass
class HeroDescriptor:
    version: str
    name: str
    hero: List[str]
    hero_deck: List[str]
    obligations: List[str]
    nemesis_set: List[str]
    player_deck: List[str] = field(default_factory=lambda: [])
    aspect: str = ""
    aspect2: str = ""

    def UpdateVersion(self):
        pass
