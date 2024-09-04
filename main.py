import requests
import asyncio
from datetime import datetime
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived
import logging

# 默认配置
config = {
    'bili_live_idx': ['479308514'],
    'notify_users': [],
    'notify_groups': []
}

bili_url = "https://api.bilibili.com/x/space/app/index"
live_cache = {}

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"请求错误: {e}")
        return None

async def cache():
    for uid in config['bili_live_idx']:
        resp_json = get_bili_status(uid)
        if resp_json is None:
            continue
        status = resp_json['data']['info']['live']['liveStatus']
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if uid not in live_cache:
            live_cache[uid] = {'status': 'false', 'last_update': current_time}
        if live_cache[uid]['status'] == 'true' and status == 0:
            live_cache[uid] = {'status': 'false', 'last_update': current_time}
            message = f"B站用户 {uid} 直播已结束。结束时间: {current_time}"
            await notify_users_and_groups(message)
            logger.info(message)
        elif live_cache[uid]['status'] == 'false' and status == 1:
            live_cache[uid] = {'status': 'true', 'last_update': current_time}
            title = f"您关注的 {resp_json['data']['info']['name']} 开播了!"
            message = f"直播标题: {resp_json['data']['info']['live']['title']}\n{resp_json['data']['info']['live']['url']}\n开播时间: {current_time}"
            await notify_users_and_groups(f"通知: {title}\n{message}")
            logger.info(f"通知: {title}\n{message}")
        else:
            logger.info(f"用户 {uid} 状态未变。当前状态: {'直播中' if status == 1 else '未直播'}。检查时间: {current_time}")

async def notify_users_and_groups(message):
    for user_id in config['notify_users']:
        logger.info(f"通知用户 {user_id}: {message}")
        await send_message("person", user_id, message)

    for group_id in config['notify_groups']:
        logger.info(f"通知群组 {group_id}: {message}")
        await send_message("group", group_id, message)

async def send_message(target_type, target_id, message):
    # 使用 ctx.send_message 发送消息
    try:
        await ctx.send_message(target_type, target_id, message)
        logger.info(f"消息发送成功: {target_id}")
    except Exception as e:
        logger.error(f"消息发送失败: {target_id}, 错误: {e}")

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
            await ctx.reply("UID 必须是数字。")
            ctx.prevent_default()
            return
        if uid not in config['bili_live_idx']:
            config['bili_live_idx'].append(uid)
            await ctx.reply(f"B站用户 {uid} 已添加。")
        else:
            await ctx.reply(f"B站用户 {uid} 已存在。")
        ctx.prevent_default()

    async def remove_bili_uid(self, ctx: EventContext, uid):
        if not uid.isdigit():
            await ctx.reply("UID 必须是数字。")
            ctx.prevent_default()
            return
        if uid in config['bili_live_idx']:
            config['bili_live_idx'].remove(uid)
            await ctx.reply(f"B站用户 {uid} 已删除。")
        else:
            await ctx.reply(f"B站用户 {uid} 不存在。")
        ctx.prevent_default()

    async def add_notify_user(self, ctx: EventContext, user_id):
        if user_id not in config['notify_users']:
            config['notify_users'].append(user_id)
            await ctx.reply(f"通知用户 {user_id} 已添加。")
        else:
            await ctx.reply(f"通知用户 {user_id} 已存在。")
        ctx.prevent_default()

    async def remove_notify_user(self, ctx: EventContext, user_id):
        if user_id in config['notify_users']:
            config['notify_users'].remove(user_id)
            await ctx.reply(f"通知用户 {user_id} 已删除。")
        else:
            await ctx.reply(f"通知用户 {user_id} 不存在。")
        ctx.prevent_default()

    async def add_notify_group(self, ctx: EventContext, group_id):
        if group_id not in config['notify_groups']:
            config['notify_groups'].append(group_id)
            await ctx.reply(f"通知群组 {group_id} 已添加。")
        else:
            await ctx.reply(f"通知群组 {group_id} 已存在。")
        ctx.prevent_default()

    async def remove_notify_group(self, ctx: EventContext, group_id):
        if group_id in config['notify_groups']:
            config['notify_groups'].remove(group_id)
            await ctx.reply(f"通知群组 {group_id} 已删除。")
        else:
            await ctx.reply(f"通知群组 {group_id} 不存在。")
        ctx.prevent_default()

    async def live_status(self, ctx: EventContext):
        await cache()  # 先进行一次检查
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status = '直播中' if live_cache.get(uid, {}).get('status', 'false') == 'true' else '未直播'
            last_update = live_cache.get(uid, {}).get('last_update', '无记录')
            status_message += f"B站用户 {uid}: {status}（最后更新: {last_update}）\n"
        await ctx.reply(status_message)
        ctx.prevent_default()

    async def show_notify_list(self, ctx: EventContext):
        user_list = "\n".join(config['notify_users']) if config['notify_users'] else "无"
        group_list = "\n".join(config['notify_groups']) if config['notify_groups'] else "无"
        message = f"当前通知用户:\n{user_list}\n\n当前通知群组:\n{group_list}"
        await ctx.reply(message)
        ctx.prevent_default()

    @handler(PersonNormalMessageReceived)
    async def handle_person_message(self, ctx: EventContext):
        event = ctx.event
        msg = event.text_message.strip()
        if msg == "hello":
            await ctx.reply(f"你好呀, {event.sender_id}!")
            ctx.prevent_default()
        elif msg.startswith("添加UID"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的B站用户UID。格式：添加UID 23333")
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.add_bili_uid(ctx, uid)
        elif msg.startswith("删除UID"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的B站用户UID。格式：删除UID 23333")
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.remove_bili_uid(ctx, uid)
        elif msg.startswith("添加通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的通知用户ID。格式：添加通知用户 12345")
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.add_notify_user(ctx, user_id)
        elif msg.startswith("删除通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的通知用户ID。格式：删除通知用户 12345")
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.remove_notify_user(ctx, user_id)
        elif msg.startswith("添加通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的通知群组ID。格式：添加通知群组 12345")
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.add_notify_group(ctx, group_id)
        elif msg.startswith("删除通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的通知群组ID。格式：删除通知群组 12345")
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.remove_notify_group(ctx, group_id)
        elif msg == "直播状态":
            await self.live_status(ctx)
        elif msg == "查看通知列表":
            await self.show_notify_list(ctx)

    @handler(GroupNormalMessageReceived)
    async def handle_group_message(self, ctx: EventContext):
        event = ctx.event
        msg = event.text_message.strip()
        if msg == "hello":
            await ctx.reply("hello, everyone!")
            ctx.prevent_default()
        elif msg.startswith("添加UID"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的B站用户UID。格式：添加UID 23333")
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.add_bili_uid(ctx, uid)
        elif msg.startswith("删除UID"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的B站用户UID。格式：删除UID 23333")
                ctx.prevent_default()
                return
            uid = parts[1]
            await self.remove_bili_uid(ctx, uid)
        elif msg.startswith("添加通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的通知用户ID。格式：添加通知用户 12345")
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.add_notify_user(ctx, user_id)
        elif msg.startswith("删除通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的通知用户ID。格式：删除通知用户 12345")
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.remove_notify_user(ctx, user_id)
        elif msg.startswith("添加通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要添加的通知群组ID。格式：添加通知群组 12345")
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.add_notify_group(ctx, group_id)
        elif msg.startswith("删除通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                await ctx.reply("请提供要删除的通知群组ID。格式：删除通知群组 12345")
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.remove_notify_group(ctx, group_id)
        elif msg == "直播状态":
            await self.live_status(ctx)
        elif msg == "查看通知列表":
            await self.show_notify_list(ctx)
