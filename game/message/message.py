from typing_extensions import NotRequired
from core import *
from game.card.face import *
from game.message import *
from game.effect import *
from game.world import *
from game.player import *
from game.object import Object
from engine.log import Log
from engine.lib import TransText
from game.ability.condition import *

CATEGORY_NAME = "MESSAGE"

class Message2(Object):

    SOUND_NAMES = Literal['', 'carddrop', 'activate', 'draw', 'damage', 'equip', 'set', 'negate', 'token', 'reveal', 'destroyed', 'flip', 'shuffle', 'addcounter', 'phase', 'nextturn', 'removecounter', 'gainlp', 'target', 'banished', 'directattack', 'cardpick']

    class MessageKwargs(TypedDict):
        world: 'World'
        send_resolve_message: NotRequired[bool]

    def __init__(self, **kwargs: Unpack[MessageKwargs]) -> None:
        from game.message.message_type import CheckNoneMessage

        world = kwargs.get('world', None)
        assert world != None

        if isinstance(self, CheckNoneMessage):
            category = 'check_message'
        else:
            category = 'message'

        super().__init__(category, world)

        send_resolve_message = kwargs.get('send_resolve_message', True)

        self.once_per_event_effects: List['Effect'] = []
        self.send_resolve_message = send_resolve_message

        self.prompt: TransText|None = None
        self.related_faces: Set['CardFace'] = set()
        self.on_events: Set['Type[OnEvent.Base]'] = set()

        if category == 'message':
            Log.DebugSilent("MESSAGE", self)

    def __repr__(self) -> str:
        return f'({self.object_id}) {self.name}'

    def AddRelatedFace(self, *faces: 'CardFace|Player|Effect|None'):
        from game.card.face.card_face import CardFace
        from game.effect import Effect
        from game.player import Player
        for face in faces:
            if isinstance(face, Player):
                self.related_faces.add(face.GetIdentity())
            elif isinstance(face, Effect):
                self.related_faces.add(face.this)
            elif isinstance(face, CardFace):
                self.related_faces.add(face)

    def TriggerOnEvent(self, on_event: Type['OnEvent.Base']):
        self.on_events.add(on_event)

    def Send(self):
        from game.message.message_type import CardStateUpdatedMessage, CheckNoneMessage

        if not self.world.is_game_over:
            if isinstance(self, CardStateUpdatedMessage):
                self.world.event_manager.StackMessage(self)
            elif self.world.event_manager.TryQueueTimingMessage(self):
                pass
            else:
                event_manager = self.world.event_manager
                timing_depth = len(event_manager.timing_occurrences)
                event_manager.broadcasting_messages.append(self)
                try:
                    event_manager.BroadcastMessage(self)
                except Exception as exc:
                    info = Log.OnCrash(CATEGORY_NAME, exc, self.name, None)
                    self.world.render.ErrorOccurred(info)
                finally:
                    assert event_manager.broadcasting_messages[-1] is self
                    event_manager.broadcasting_messages.pop()
                    event_manager.RestoreTimingOccurrenceDepth(
                        timing_depth,
                        reason=f"message {self.name} did not close its timing occurrence",
                    )
                if not isinstance(self, CheckNoneMessage) and \
                    event_manager.stack_message:
                    event_manager.BroadcastStackMessage()
        else:
            from game.message.sender.sender import CanBeInstead
            if isinstance(self, CanBeInstead):
                self.SilentInstead()
            # Using "09032" to win the game
            # from game.message import Message
            # if isinstance(self, Message.WhenCardWouldMoveToArea):
            #     self.SetCannot()

    def GetDisplayName(self) -> str:
        return f'"{self.name}"'

    def CastTo(self, message: Type['TMP']) -> 'TMP':
        return Cast(message, self)

    @property
    def name(self) -> str:
        return type(self).__name__

    @final
    def GetReplayText(self) -> str:
        return f"m{self.object_id} {self.name}"

    @final
    def Present(self, origin_info: 'TransText|None', sound_name: 'Message2.SOUND_NAMES', *faces: 'CardFace') -> None:
        if not self.world.is_game_over:
            self.PresentInternal(origin_info, sound_name, self.name, *faces)

    @final
    def Present_Activate(self, origin_info: 'TransText|None', effect: 'Effect') -> None:
        if not self.world.is_game_over:
            self.PresentInternal(origin_info, "activate", "EffectActivate_Text", effect.this)

    @final
    def Present_PointTo(self, origin_info: 'TransText|None', sound_name: 'Message2.SOUND_NAMES', face: 'CardFace', *faces: 'CardFace') -> None:
        if not self.world.is_game_over:
            self.PresentInternal(origin_info, sound_name, "EffectActivateTo_Text", face, *faces)

    @final
    def Present_ByEffect(self, origin_info: 'TransText|None', sound_name: 'Message2.SOUND_NAMES', face: 'CardFace', effect: 'CardFace') -> None:
        return self.Present_PointTo(origin_info, sound_name, effect, face)

    @final
    def PresentGameOver(self, origin_info: 'TransText|None', sound_name: 'Message2.SOUND_NAMES', name: str, *faces: 'CardFace') -> None:
        was_skipping = False
        if self.world.controller_manager.skip.SetIsSkipping(False):
            was_skipping = True
        self.PresentInternal(origin_info, sound_name, name, *faces)
        if was_skipping:
            self.world.render.PresentForceNoWait()

    @final
    def PresentInternal(self, origin_info: 'TransText|None', sound_name: 'Message2.SOUND_NAMES', name: str, *faces: 'CardFace') -> None:
        code_info = ""
        if origin_info == None:
            origin_info = TransText("")
        self.prompt = origin_info
        # if not Build.release:
        #     file_name = inspect.getfile(type(self))
        #     first_line = inspect.getsourcelines(type(self))[1]
        #     code_info = f"{file_name}:{first_line}"
        self.world.render.Present(origin_info, sound_name, name, *faces, code_info=code_info)

