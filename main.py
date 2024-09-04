import asyncio
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived

@register(name="TestPlugin", description="Minimal Test Plugin", version="0.1", author="YourName")
class TestPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host

    async def send_message(self, host: APIHost, event, message):
        if event.context_type == "group":
            await host.send_group_message(event.context_id, message)
        else:
            await host.send_person_message(event.context_id, message)

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, event: PersonNormalMessageReceived, ctx: EventContext):
        msg = event.text_message.strip()
        if msg == "!test_command":
            await self.send_message(self.host, event, "Test command received!")

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, event: GroupNormalMessageReceived, ctx: EventContext):
        msg = event.text_message.strip()
        if msg == "!test_command":
            await self.send_message(self.host, event, "Test command received!")
