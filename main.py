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

    async def periodic_check(self):
        while True:
            await cache()
            await asyncio.sleep(60)  # 每分钟检查一次

    async def send_message(self, host: APIHost, event, message):
        if isinstance(event, PersonNormalMessageReceived):
            await host.send_person_message(event.sender_id, message)
        elif isinstance(event, GroupNormalMessageReceived):
            await host.send_group_message(event.group_id, message)

    async def add_bili_uid(self, event, host: APIHost, uid):
        if not uid.isdigit():
            await self.send_message(host, event, "UID 必须是数字。")
            return
        if uid not in config['bili_live_idx']:
            config['bili_live_idx'].append(uid)
            await self.send_message(host, event, f"B站用户 {uid} 已添加。")
        else:
            await self.send_message(host, event, f"B站用户 {uid} 已存在。")

    async def check_live(self, event, host: APIHost, kwargs):
        await cache()
        await self.send_message(host, event, "已手动检查直播状态。")

    async def live_status(self, event, host: APIHost, kwargs):
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        await self.send_message(host, event, status_message)

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, event: PersonNormalMessageReceived, ctx: EventContext):
        msg = event.text_message.strip()
        if msg.startswith("add_bili_uid"):
            await self.add_bili_uid(event, self.host, msg.split()[1])
        elif msg == "check_live":
            await self.check_live(event, self.host, {})
        elif msg == "live_status":
            await self.live_status(event, self.host, {})

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, event: GroupNormalMessageReceived, ctx: EventContext):
        msg = event.text_message.strip()
        if msg.startswith("add_bili_uid"):
            await self.add_bili_uid(event, self.host, msg.split()[1])
        elif msg == "check_live":
            await self.check_live(event, self.host, {})
        elif msg == "live_status":
            await self.live_status(event, self.host, {})
