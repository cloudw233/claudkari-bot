import asyncio
import logging
import os

import orjson as json

from core.config import CFGManager
from core.background_tasks import init_background_task
from core.extra.scheduler import load_extra_schedulers
from core.loader import load_modules, ModulesManager
from core.logger import Logger, bot_name
from core.queue import JobQueue
from core.scheduler import Scheduler
from core.constants import PrivateAssets, Secret
from core.utils.info import Info
from core.utils.web_render import check_web_render

from tomlkit.items import Table


async def init_async(start_scheduler=True) -> None:
    try:
        Info.version = os.popen('git rev-parse HEAD', 'r').read()
    except Exception:
        Logger.warning(f'Failed to get Git commit hash, is it a Git repository?')
    load_modules()
    gather_list = []
    modules = ModulesManager.return_modules_list()
    for x in modules:
        if schedules := modules[x].schedule_list.set:
            for schedule in schedules:
                Scheduler.add_job(func=schedule.function, trigger=schedule.trigger, misfire_grace_time=30,
                                  max_instance=1)
    await asyncio.gather(*gather_list)
    await init_background_task()
    if start_scheduler:
        if not Info.subprocess:
            load_extra_schedulers()
        await JobQueue.secret_append_ip()
        Scheduler.start()
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    await load_secret()
    asyncio.create_task(check_web_render())
    Logger.info(f'Hello, {bot_name}!')


async def load_secret():
    for x in CFGManager.values:
        if x.endswith('secret'):
            for y in CFGManager.values[x].keys():
                if isinstance(y, Table):
                    for z in CFGManager.values[x][y].keys():
                        Secret.add(str(CFGManager.values[x][y].get(z)).upper())
                else:
                    Secret.add(str(CFGManager.values[x][y]).upper())


async def load_prompt(bot) -> None:
    author_cache = os.path.join(PrivateAssets.path, 'cache_restart_author')
    loader_cache = os.path.join(PrivateAssets.path, '.cache_loader')
    if os.path.exists(author_cache):
        open_author_cache = open(author_cache, 'r', encoding='utf-8')
        author = json.loads(open_author_cache.read())['ID']
        open_loader_cache = open(loader_cache, 'r', encoding='utf-8')
        m = await bot.fetch_target(author)
        if m:
            if (read := open_loader_cache.read()) != '':
                await m.send_direct_message(m.parent.locale.t('loader.load.failed', detail=read))
            else:
                await m.send_direct_message(m.parent.locale.t('loader.load.success'))
            open_loader_cache.close()
            open_author_cache.close()
            os.remove(author_cache)
            os.remove(loader_cache)


__all__ = ['init_async', 'load_prompt']
