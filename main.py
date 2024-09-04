import requests
import json
import asyncio
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
from pkg.command.operator import CommandOperator, operator_class

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

@operator_class(name="AddBiliUID", help="添加B站用户UID", usage="!add_bili_uid <UID>")
class AddBiliUIDOperator(CommandOperator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, ctx: EventContext, **kwargs):
        msg = str(kwargs['message_chain']).strip()
        new_uid = msg.split(" ", 1)[1]
        if new_uid not in config['bili_live_idx']:
            config['bili_live_idx'].append(new_uid)
            await ctx.reply(f"B站用户 {new_uid} 已添加。")
        else:
            await ctx.reply(f"B站用户 {new_uid} 已存在。")

@operator_class(name="CheckLive", help="手动检查直播状态", usage="!check_live")
class CheckLiveOperator(CommandOperator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, ctx: EventContext, **kwargs):
        cache()
        await ctx.reply("已手动检查直播状态。")

@operator_class(name="LiveStatus", help="查询当前直播状态缓存", usage="!live_status")
class LiveStatusOperator(CommandOperator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, ctx: EventContext, **kwargs):
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status_message += f"B站用户 {uid}: {'直播中' if live_cache.get(uid, 'false') == 'true' else '未直播'}\n"
        await ctx.reply(status_message)

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
        pass

