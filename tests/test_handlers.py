from story_finder import messages
from story_finder.bot import Handlers


class FakeMessage:
    def __init__(self):
        self.replies: list[str] = []

    async def reply_text(self, text: str, **kwargs) -> None:
        self.replies.append(text)


class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()


class FakeContext:
    def __init__(self, args=None, error=None):
        self.args = args or []
        self.error = error


async def test_start_greets_the_owner_in_portuguese():
    update = FakeUpdate()
    await Handlers().start(update, FakeContext())
    assert update.message.replies == [messages.START]


async def test_start_mentions_the_commands_that_exist():
    update = FakeUpdate()
    await Handlers().start(update, FakeContext())
    reply = update.message.replies[0]
    assert "/add" in reply and "/list" in reply and "/remove" in reply
