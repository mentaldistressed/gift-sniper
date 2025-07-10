import asyncio
from math import gcd

from structlog.typing import FilteringBoundLogger

from aiogram import Bot 

from src.redis import RedisStorage



async def process_user_batch(bot: Bot, users: list, gift_data: dict, logger: FilteringBoundLogger):
    for user in users:
        try:
            while not await bot.database.get_gift_delivery(int(gift_data["id"]), user.id):
                delivery = await bot.database.create_gift_delivery(gift_data["id"], user.id)
                if await bot.database.user_buy_gift(gift_data["amount"], user.id):
                    await bot.send_gift(
                        user.id, str(gift_data["id"])
                    )
                    await logger.ainfo(f'gift {gift_data["id"]} delivered to user {user.id}')
                    await bot.database.mark_gift_delivered(delivery.id)
        except Exception as e:
            await logger.aerror(f'Failed to deliver gift {gift_data["id"]} to user {user.id}: {e}')
            continue


async def check_new_gifts(bot: Bot, redis: RedisStorage, logger: FilteringBoundLogger, vip_only: bool = False) -> bool:
    try:
        result = await bot.get_available_gifts()
        validate_result = []

        pack_name = "giftomatic_pack_by_GiftomaticRobot"
        pack_title = "💎 @GiftomaticRobot"
        try:
            await bot.get_sticker_set(name=pack_name)
            has_pack = True
        except Exception:
            has_pack = False

        if not has_pack:
            await bot.create_new_sticker_set(
                user_id=bot.config.owner_bot_user_id,  # ID создателя пака
                name=pack_name,
                title=pack_title,
                stickers=[],
                sticker_format="static"
            )
            await logger.ainfo(f"Emoji‑пак {pack_title} создан")

        for item in result.gifts:
            gift_id = int(item.id)
            if redis.add_gift(gift_id, vip=vip_only):
                await logger.ainfo(f'new gift registered: {gift_id}')
                validate_result.append({
                    "id": gift_id,
                    "count": item.total_count or 1_000_000,
                    "amount": item.star_count,
                    "image_url": item.image_url
                })

        if validate_result:
            sorted_gifts = sorted(validate_result, key=lambda x: (x["count"], -x["amount"]))
            all_users = await bot.database.get_user_updator(vip_only)

            for gift_data in sorted_gifts:
                file_unique_id = await bot.download_image_and_get_file_unique_id(gift_data["image_url"])
                existing = await bot.sticker_unique_exists(pack_name, file_unique_id)
                if not existing:
                    await bot.add_sticker_to_set(
                        user_id=bot.config.owner_bot_user_id,
                        name=pack_name,
                        png_sticker=file_unique_id,
                        emojis=f"gift{gift_data['id']}"
                    )
                    await logger.ainfo(f"Добавлен sticker для gift {gift_data['id']}")

                text = (
                    f"🎁 *Новый подарок!* 🎁\n\n"
                    f"💎 *Цена:* {gift_data['amount']}⭐️\n"
                    f"📦 *Осталось:* {gift_data['count']}\n"
                )
                emoji_for_post = f"gift{gift_data['id']}"
                await bot.send_message(
                    chat_id=bot.config.channel,
                    text=text + emoji_for_post,
                    parse_mode="Markdown"
                )

                tasks = []
                for i in range(0, len(all_users), bot.config.bach_size):
                    user_batch = all_users[i:i + bot.config.bach_size]
                    tasks.append(
                        asyncio.create_task(
                            process_user_batch(bot, user_batch, gift_data, logger)
                        )
                    )
                if tasks:
                    await asyncio.gather(*tasks)

        return True

    except Exception as e:
        await logger.aerror(f"Error checking gifts: {e}")
        return False


async def background_gift_updator(
        bot: Bot, 
        redis: RedisStorage, 
        logger: FilteringBoundLogger, 
        vip_poll_interval: int,
        default_poll_interval: int
    ):
    
    base_interval = gcd(vip_poll_interval, default_poll_interval)
    cycles_until_default = default_poll_interval // base_interval
    cycles_until_vip = vip_poll_interval // base_interval
    current_cycle = 0
    
    await logger.ainfo(f'base interval: {base_interval}, default: {default_poll_interval}, vip: {vip_poll_interval}')

    while True:
        is_vip_cycle = current_cycle % cycles_until_vip == 0
        is_default_cycle = current_cycle % cycles_until_default == 0
    
        if is_default_cycle:
            await check_new_gifts(bot, redis, logger, vip_only=False)

        elif is_vip_cycle:
            await check_new_gifts(bot, redis, logger, vip_only=True)
            
        current_cycle += 1
        await asyncio.sleep(base_interval)