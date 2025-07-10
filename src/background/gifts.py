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

        for item in result.gifts:
            gift_id = int(item.id)
            if redis.add_gift(gift_id, vip=vip_only):
                await logger.ainfo(f'new gift registered: {gift_id} for {"vip" if vip_only else "vip and default"} users')
                validate_result.append({"id": gift_id, "count": item.total_count if item.total_count else 1_000_000, "amount": item.star_count})
        
        if validate_result:
            sorted_gifts = sorted(validate_result, key=lambda x: (x["count"], -x["amount"]))
            all_users = await bot.database.get_user_updator(vip_only)
            
            for gift_data in sorted_gifts:
                tasks = []
                
                for i in range(0, len(all_users), bot.config.bach_size):
                    user_batch = all_users[i:i + bot.config.bach_size]
                    task = asyncio.create_task(
                        process_user_batch(bot, user_batch, gift_data, logger)
                    )
                    tasks.append(task)
                    
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