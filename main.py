import requests
import json
import asyncio
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

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
class BiliBiliWatcherPlugin(Plugin):

    def __init__(self, plugin_host: PluginHost):
        self.host = plugin_host
        asyncio.create_task(self.periodic_check())

    async def periodic_check(self):
        while True:
            cache()
            await asyncio.sleep(60)  # 每分钟检查一次

    @on(PersonMessageReceived)
    @on(GroupMessageReceived)
    async def message_received(self, event: EventContext, host: PluginHost, **kwargs):
        msg = str(kwargs['message_chain']).strip()
        await self.handle_message(event, host, msg, kwargs)

    async def handle_message(self, event: EventContext, host: PluginHost, msg: str, kwargs):
        if msg.startswith("!add_bili_uid "):
            new_uid = msg.split(" ", 1)[1]
            if new_uid not in config['bili_live_idx']:
                config['bili_live_idx'].append(new_uid)
                await host.send_message(kwargs['launcher_id'], [f"B站用户 {new_uid} 已添加。"])
            else:
                await host.send_message(kwargs['launcher_id'], [f"B站用户 {new_uid} 已存在。"])
            event.prevent_default()
            event.prevent_postorder()
        elif msg == "!check_live":
            await self.check_live_status()
            await host.send_message(kwargs['launcher_id'], ["已手动检查直播状态。"])
            event.prevent_default()
            event.prevent_postorder()
        elif msg == "!live_status":
            status_message = self.get_live_status_message()
            await host.send_message(kwargs['launcher_id'], [status_message])
            event.prevent_default()
            event.prevent_postorder()

    def get_live_status_message(self):
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        return status_message

    async def check_live_status(self):
        cache()
