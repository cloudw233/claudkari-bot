import traceback

from core.builtins import Bot
from core.component import module
from modules.wiki.utils.dbutils import WikiTargetInfo, Audit
from modules.wiki.utils.wikilib import WikiLib, WhatAreUDoingError, PageInfo, InvalidWikiError, QueryInfo
from .ab import ab
from .ab_qq import ab_qq
from .newbie import newbie
from .rc import rc
from .rc_qq import rc_qq

rc_ = module('rc', developers=['OasisAkari'])


@rc_.command(['{{wiki.help.rc}}',
             'legacy [<count>] {{wiki.help.rc.legacy}}'],
           available_for=['QQ', 'QQ|Group'])
async def rc_loader(msg: Bot.MessageSession, count: int=5):
    start_wiki = WikiTargetInfo(msg).get_start_wiki()
    if not start_wiki:
        await msg.finish(msg.locale.t('wiki.message.not_set'))
    legacy = True
    if not msg.parsed_msg and msg.Feature.forward and msg.target.target_from == 'QQ|Group':
        try:
            nodelist = await rc_qq(msg, start_wiki)
            await msg.fake_forward_msg(nodelist)
            legacy = False
        except Exception:
            traceback.print_exc()
            await msg.send_message(msg.locale.t('wiki.message.rollback'))
    if legacy:
        res = await rc(msg, start_wiki, count)
        await msg.finish(res)


@rc_.command(['[<count>] {{wiki.help.rc}}'],
           exclude_from=['QQ', 'QQ|Group'])
async def rc_loader(msg: Bot.MessageSession, count: int=5):
    start_wiki = WikiTargetInfo(msg).get_start_wiki()
    if not start_wiki:
        await msg.finish(msg.locale.t('wiki.message.not_set'))
    res = await rc(msg, start_wiki, count)
    await msg.finish(res)


a = module('ab', developers=['OasisAkari'])


@a.command(['{{wiki.help.ab}}',
           'legacy [<count>] {{wiki.help.ab.legacy}}'],
           available_for=['QQ', 'QQ|Group'])
async def ab_loader(msg: Bot.MessageSession, count: int=5):
    start_wiki = WikiTargetInfo(msg).get_start_wiki()
    if not start_wiki:
        await msg.finish(msg.locale.t('wiki.message.not_set'))
    legacy = True
    if not msg.parsed_msg and msg.Feature.forward and msg.target.target_from == 'QQ|Group':
        try:
            nodelist = await ab_qq(msg, start_wiki)
            await msg.fake_forward_msg(nodelist)
            legacy = False
        except Exception:
            traceback.print_exc()
            await msg.send_message(msg.locale.t('wiki.message.rollback'))
    if legacy:
        res = await ab(msg, start_wiki, count)
        await msg.finish(res)


@a.command(['[<count>] {{wiki.help.ab}}'],
           exclude_from=['QQ', 'QQ|Group'])
async def ab_loader(msg: Bot.MessageSession, count: int=5):
    start_wiki = WikiTargetInfo(msg).get_start_wiki()
    if not start_wiki:
        await msg.finish(msg.locale.t('wiki.message.not_set'))
    res = await ab(msg, start_wiki, count)
    await msg.finish(res)


n = module('newbie', developers=['OasisAkari'])


@n.command('[<count>] {{wiki.help.newbie}}')
async def newbie_loader(msg: Bot.MessageSession, count: int=5):
    start_wiki = WikiTargetInfo(msg).get_start_wiki()
    if not start_wiki:
        await msg.finish(msg.locale.t('wiki.message.not_set'))
    res = await newbie(msg, start_wiki, count)
    await msg.finish(res)
