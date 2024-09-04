import aiohttp
import asyncio
import logging
from datetime import datetime
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived
import mirai  # 确保导入 mirai 库

# 默认配置
config = {
    'bili_live_idx': ['479308514'],
    'notify_users': [],
    'notify_groups': []
}

bili_url = "https://api.bilibili.com/x/space/app/index"
live_cache = {}

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_bili_status(uid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(bili_url, params={'mid': uid}, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"请求错误: {e}")
        return None

async def cache(ctx):
    for uid in config['bili_live_idx']:
        resp_json = await get_bili_status(uid)
        if resp_json is None:
            continue
        status = resp_json['data']['info']['live']['liveStatus']
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if uid not in live_cache:
            live_cache[uid] = {'status': 'false', 'last_update': current_time}
        if live_cache[uid]['status'] == 'true' and status == 0:
            live_cache[uid] = {'status': 'false', 'last_update': current_time}
            message = f"B站用户 {uid} 直播已结束。结束时间: {current_time}"
            await notify_users_and_groups(ctx, message)
            logger.info(message)
        elif live_cache[uid]['status'] == 'false' and status == 1:
            live_cache[uid] = {'status': 'true', 'last_update': current_time}
            title = f"您关注的 {resp_json['data']['info']['name']} 开播了!"
            message = f"直播标题: {resp_json['data']['info']['live']['title']}\n{resp_json['data']['info']['live']['url']}\n开播时间: {current_time}"
            await notify_users_and_groups(ctx, f"通知: {title}\n{message}")
            logger.info(f"通知: {title}\n{message}")
        else:
            logger.info(f"用户 {uid} 状态未变。当前状态: {'直播中' if status == 1 else '未直播'}。检查时间: {current_time}")

async def notify_users_and_groups(ctx, message):
    for user_id in config['notify_users']:
        logger.info(f"通知用户 {user_id}: {message}")
        await send_message(ctx, "person", user_id, message)

    for group_id in config['notify_groups']:
        logger.info(f"通知群组 {group_id}: {message}")
        await send_message(ctx, "group", group_id, message)

async def send_message(ctx, target_type, target_id, message):
    # 这里实现发送消息的逻辑
    message_chain = [mirai.Plain(message)]
    if target_type == "person":
        await ctx.send_message("person", target_id, message_chain)
    elif target_type == "group":
        await ctx.send_message("group", target_id, message_chain)

@register(name="BiliBiliWatcher", description="BiliBili Live Notifier", version="0.1", author="YourName")
class BiliBiliWatcherPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.host = host
        asyncio.create_task(self.periodic_check())

    async def initialize(self):
        pass

    async def periodic_check(self):
        while True:
            await cache(None)  # 定期检查时不需要上下文
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

    async def add_notify_user(self, ctx: EventContext, user_id):
        if user_id not in config['notify_users']:
            config['notify_users'].append(user_id)
            ctx.add_return("reply", [f"通知用户 {user_id} 已添加。"])
        else:
            ctx.add_return("reply", [f"通知用户 {user_id} 已存在。"])
        ctx.prevent_default()

    async def remove_notify_user(self, ctx: EventContext, user_id):
        if user_id in config['notify_users']:
            config['notify_users'].remove(user_id)
            ctx.add_return("reply", [f"通知用户 {user_id} 已删除。"])
        else:
            ctx.add_return("reply", [f"通知用户 {user_id} 不存在。"])
        ctx.prevent_default()

    async def add_notify_group(self, ctx: EventContext, group_id):
        if group_id not in config['notify_groups']:
            config['notify_groups'].append(group_id)
            ctx.add_return("reply", [f"通知群组 {group_id} 已添加。"])
        else:
            ctx.add_return("reply", [f"通知群组 {group_id} 已存在。"])
        ctx.prevent_default()

    async def remove_notify_group(self, ctx: EventContext, group_id):
        if group_id in config['notify_groups']:
            config['notify_groups'].remove(group_id)
            ctx.add_return("reply", [f"通知群组 {group_id} 已删除。"])
        else:
            ctx.add_return("reply", [f"通知群组 {group_id} 不存在。"])
        ctx.prevent_default()

    async def live_status(self, ctx: EventContext):
        await cache(ctx)  # 先进行一次检查
        status_message = "当前直播状态缓存：\n"
        for uid in config['bili_live_idx']:
            status = '直播中' if live_cache.get(uid, {}).get('status', 'true') == 'true' else '未直播'
            last_update = live_cache.get(uid, {}).get('last_update', '无记录')
            status_message += f"B站用户 {uid}: {status}（最后更新: {last_update}）\n"
        ctx.add_return("reply", [status_message])
        ctx.prevent_default()

    async def show_notify_list(self, ctx: EventContext):
        user_list = "\n".join(config['notify_users']) if config['notify_users'] else "无"
        group_list = "\n".join(config['notify_groups']) if config['notify_groups'] else "无"
        message = f"当前通知用户:\n{user_list}\n\n当前通知群组:\n{group_list}"
        ctx.add_return("reply", [message])
        ctx.prevent_default()

    # 当收到个人消息时触发
    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message  # 这里的 event 即为 PersonNormalMessageReceived 的对象
        if msg == "hello":  # 如果消息为hello
            # 输出调试信息
            logger.debug("hello, {}".format(ctx.event.sender_id))
            # 回复消息 "hello, <发送者id>!"
            ctx.add_return("reply", ["hello, {}!".format(ctx.event.sender_id)])
            # 阻止该事件默认行为（向接口获取回复）
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
        elif msg.startswith("添加通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的通知用户ID。格式：添加通知用户 12345"])
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.add_notify_user(ctx, user_id)
        elif msg.startswith("删除通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的通知用户ID。格式：删除通知用户 12345"])
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.remove_notify_user(ctx, user_id)
        elif msg.startswith("添加通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的通知群组ID。格式：添加通知群组 12345"])
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.add_notify_group(ctx, group_id)
        elif msg.startswith("删除通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的通知群组ID。格式：删除通知群组 12345"])
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.remove_notify_group(ctx, group_id)
        elif msg == "直播状态":
            await self.live_status(ctx)
        elif msg == "查看通知列表":
            await self.show_notify_list(ctx)

    # 当收到群消息时触发
    @handler(GroupNormalMessageReceived)
    async def group_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message  # 这里的 event 即为 GroupNormalMessageReceived 的对象
        if msg == "hello":  # 如果消息为hello
            # 输出调试信息
            logger.debug("hello, {}".format(ctx.event.sender_id))
            # 回复消息 "hello, everyone!"
            ctx.add_return("reply", ["hello, everyone!"])
            # 阻止该事件默认行为（向接口获取回复）
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
        elif msg.startswith("添加通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的通知用户ID。格式：添加通知用户 12345"])
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.add_notify_user(ctx, user_id)
        elif msg.startswith("删除通知用户"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的通知用户ID。格式：删除通知用户 12345"])
                ctx.prevent_default()
                return
            user_id = parts[1]
            await self.remove_notify_user(ctx, user_id)
        elif msg.startswith("添加通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要添加的通知群组ID。格式：添加通知群组 12345"])
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.add_notify_group(ctx, group_id)
        elif msg.startswith("删除通知群组"):
            parts = msg.split()
            if len(parts) < 2:
                ctx.add_return("reply", ["请提供要删除的通知群组ID。格式：删除通知群组 12345"])
                ctx.prevent_default()
                return
            group_id = parts[1]
            await self.remove_notify_group(ctx, group_id)
        elif msg == "直播状态":
            await self.live_status(ctx)
        elif msg == "查看通知列表":
            await self.show_notify_list(ctx)
