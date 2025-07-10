################################
#             dev:             #
#          t.me/awixa          #
################################


import asyncio, datetime

from structlog import get_logger
from structlog.typing import FilteringBoundLogger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.config import ConfigReader
from src.handlers import get_all_routers
from src.background import background_gift_updator
from src.redis import RedisStorage
from src.data.database import Database


async def print_info(version: str, bot: Bot, logger: FilteringBoundLogger):
    me = await bot.get_me()
    await logger.ainfo(f'start bot: @{me.username}, dev: t.me/awixa, version: {version}')

async def main():
    loader_conf = ConfigReader()
    config = loader_conf._load()
    logger = get_logger()

    redis = RedisStorage(config.redis.host, config.redis.port)

    bot = Bot(
        token=config.bot_token, 
        default=DefaultBotProperties(parse_mode=config.parse_mode)
    )
    dp = Dispatcher()

    bot.logger = logger 
    bot.config = config
    bot.startup_date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    bot.database = Database()
    await bot.database.init_db()

    await print_info(config.version, bot, logger)

    for router, rname in get_all_routers():
        dp.include_router(router)
        await logger.adebug(f'load router', router=rname)

    asyncio.create_task(background_gift_updator(
        bot, redis, logger, 
        config.vip_poll_interval, config.default_poll_interval
    ))

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())