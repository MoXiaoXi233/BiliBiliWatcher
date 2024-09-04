import requests
import asyncio
import logging
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived

# 默认配置
config = {
    'bili_live_idx': ['479308514']
}

bili_url = "https://api.bilibili.com/x/space/app/index"
live_cache = {}

def get_bili_status(uid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com"
    }
    try:
        response = requests.get(bili_url, params={'mid': uid}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None

async def cache():
    for uid in config['bili_live_idx']:
        resp_json = get_bili_status(uid)
        if resp_json is None:
            continue
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
        asyncio.create_task(self.periodic_check())

    async def initialize(self):
        pass

    async def periodic_check(self):
        while True:
            await cache()
            await asyncio.sleep(60)  # 每分钟检查一次

    async def add_bili_uid(self, ctx: EventContext, uid):
        if not uid.isdigit():
            ctx.add_return("reply", ["UID 必须是数字。"])
            ctx.prevent_default()
            return
        if uid not in config['bili_live_idx']:
            config['bili_live_idx'].append(uid)
            ctx.add_return("reply", [f"B站用户 {uid} 已添加。"])
        else:
            ctx.add_return("reply", [f"B站用户 {uid} 已存在。"])
        ctx.prevent_default()

    async def remove_bili_uid(self, ctx: EventContext, uid):
        if not uid.isdigit():
            ctx.add_return("reply", ["UID 必须是数字。"])
            ctx.prevent_default()
            return
        if uid in config['bili_live_idx']:
            config['bili_live_idx'].remove(uid)
            ctx.add_return("reply", [f"B站用户 {uid} 已删除。"])
        else:
            ctx.add_return("reply", [f"B站用户 {uid} 不存在。"])
        ctx.prevent_default()

    async def live_status(self, ctx: EventContext):
        await cache()  # 先进行一次检查
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        ctx.add_return("reply", [status_message])
        ctx.prevent_default()

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, ctx: EventContext):
        event = ctx.event
        msg = event.text_message.strip()
        if msg == "hello":
            ctx.add_return("reply", [f"你好呀, {event.sender_id}!"])
            ctx.prevent_default()
        elif msg.startswith("添加UID"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的B站用户UID。格式：添加UID 23333"])
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.add_bili_uid(ctx, uid)
        elif msg.startswith("删除UID"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的B站用户UID。格式：删除UID 23333"])
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.remove_bili_uid(ctx, uid)
        elif msg == "直播状态":
            await self.live_status(ctx)

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        event = ctx.event
        msg = event.text_message.strip()
        if msg == "hello":
            ctx.add_return("reply", ["hello, everyone!"])
            ctx.prevent_default()
        elif msg.startswith("添加UID"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的B站用户UID。格式：添加UID 23333"])
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.add_bili_uid(ctx, uid)
        elif msg.startswith("删除UID"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的B站用户UID。格式：删除UID 23333"])
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.remove_bili_uid(ctx, uid)
        elif msg == "直播状态":
            await self.live_status(ctx)
