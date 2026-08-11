import asyncio
from livekit import agents

def test():
    print(hasattr(agents.voice.room_io.RoomIO, 'set_participant'))
test()
