import requests
import asyncio
import logging
import traceback
from pkg.plugin.models import Plugin, register, on, PersonMessageReceived, GroupMessageReceived
from pkg.plugin.host import PluginHost

# 默认配置
config = {
    'bili_live_idx': ['479308514']
}

bili_url = "https://api.bilibili.com/x/space/app/index"
live_cache = {}

def get_bili_status(uid):
    try:
        response = requests.get(bili_url, params={'mid': uid})
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
class BiliBiliWatcherPlugin(Plugin):

    def __init__(self, plugin_host: PluginHost):
        self.host = plugin_host
        asyncio.create_task(self.periodic_check())

    async def periodic_check(self):
        while True:
            await cache()
            await asyncio.sleep(60)  # 每分钟检查一次

    @on(PersonMessageReceived)
    @on(GroupMessageReceived)
    async def handle_message(self, event, host: PluginHost, message_chain, **kwargs):
        try:
            text = str(message_chain).strip()
            if text.startswith("!add_bili_uid"):
                event.prevent_default()
                event.prevent_postorder()
                await self.add_bili_uid(event, host, text.split()[1])
            elif text == "!check_live":
                event.prevent_default()
                event.prevent_postorder()
                await self.check_live(event, host, kwargs)
            elif text == "!live_status":
                event.prevent_default()
                event.prevent_postorder()
                await self.live_status(event, host, kwargs)
        except Exception as e:
            logging.error(traceback.format_exc())

    async def add_bili_uid(self, event, host: PluginHost, uid):
        if not uid.isdigit():
            await self.send_message(host, event, "UID 必须是数字。")
            return
        if uid not in config['bili_live_idx']:
            config['bili_live_idx'].append(uid)
            await self.send_message(host, event, f"B站用户 {uid} 已添加。")
        else:
            await self.send_message(host, event, f"B站用户 {uid} 已存在。")

    async def check_live(self, event, host: PluginHost, kwargs):
        await cache()
        await self.send_message(host, event, "已手动检查直播状态。")

    async def live_status(self, event, host: PluginHost, kwargs):
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        await self.send_message(host, event, status_message)

    async def send_message(self, host: PluginHost, event, message):
        if event.context_type == "group":
            await host.send_group_message(event.context_id, message)
        else:
            await host.send_person_message(event.context_id, message)

    # 插件卸载时触发
    def __del__(self):
        pass
