import requests
import json
import asyncio
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived

# 默认配置
config = {
    'bili_live_idx': ['479308514']
}

bili_url = "https://api.bilibili.com/x/space/app/index"

live_cache = {}

def get_bili_status(uid):
    return requests.get(bili_url, params={'mid': uid}).json()

def cache():
    for uid in config['bili_live_idx']:
        resp_json = get_bili_status(uid)
        status = resp_json['data']['info']['live']['liveStatus']
        if uid not in live_cache:
            live_cache[uid] = 'true'
        if live_cache[uid] == 'true':
            if status == 0:
                live_cache[uid] = 'false'
        else:
            if status == 1:
                live_cache[uid] = 'true'
                title = f"您关注的{resp_json['data']['info']['name']}开播了!"
                message = f"直播标题:{resp_json['data']['info']['live']['title']}\n{resp_json['data']['info']['live']['url']}"
                print(f"通知: {title}\n{message}")

@register(name="BiliBiliWatcher", description="BiliBili Live Notifier", version="0.1", author="YourName")
class BiliBiliWatcherPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host

    async def initialize(self):
        # 启动一个异步任务定期检查直播状态
        asyncio.create_task(self.periodic_check())

    async def periodic_check(self):
        while True:
            cache()
            await asyncio.sleep(60)  # 每分钟检查一次

    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message.strip()
        await self.handle_message(ctx, msg)

    @handler(GroupNormalMessageReceived)
    async def group_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message.strip()
        await self.handle_message(ctx, msg)

    async def handle_message(self, ctx: EventContext, msg: str):
        if msg.startswith("!add_bili_uid "):
            new_uid = msg.split(" ", 1)[1]
            if new_uid not in config['bili_live_idx']:
                config['bili_live_idx'].append(new_uid)
                ctx.add_return("reply", [f"B站用户 {new_uid} 已添加。"])
            else:
                ctx.add_return("reply", [f"B站用户 {new_uid} 已存在。"])
            ctx.prevent_default()
        elif msg == "!check_live":
            await self.check_live_status()
            ctx.add_return("reply", ["已手动检查直播状态。"])
            ctx.prevent_default()
        elif msg == "!live_status":
            status_message = self.get_live_status_message()
            ctx.add_return("reply", [status_message])
            ctx.prevent_default()

    def get_live_status_message(self):
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        return status_message

    async def check_live_status(self):
        cache()
