import importlib
import os
import re
import sys
import traceback
from typing import Dict, Union

from config import Config

from core.builtins import PrivateAssets
from core.logger import Logger
from core.types import Module
from core.types.module.component_meta import CommandMeta, RegexMeta, ScheduleMeta, TaskMeta
from core.utils.i18n import load_locale_file

load_dir_path = os.path.abspath('./modules/')
all_modules = []
current_unloaded_modules = []
err_modules = []


def load_modules():
    unloaded_modules = Config('unloaded_modules')
    if not unloaded_modules:
        unloaded_modules = []
    err_prompt = []
    locale_err = load_locale_file()
    if locale_err:
        locale_err.append('i18n:')
        err_prompt.append('\n'.join(locale_err))
    fun_file = None
    dir_list = os.listdir(load_dir_path)
    for file_name in dir_list:
        try:
            file_path = os.path.join(load_dir_path, file_name)
            fun_file = None
            if os.path.isdir(file_path):
                if file_name[0] != '_':
                    fun_file = file_name
            elif os.path.isfile(file_path):
                if file_name[0] != '_' and file_name.endswith('.py'):
                    fun_file = file_name[:-3]
            if fun_file is not None:
                Logger.info(f'Loading modules.{fun_file}...')
                all_modules.append(fun_file)
                if fun_file in unloaded_modules:
                    Logger.warn(f'Skipped modules.{fun_file}!')
                    current_unloaded_modules.append(fun_file)
                    continue
                modules = 'modules.' + fun_file
                importlib.import_module(modules)
                Logger.info(f'Succeeded loaded modules.{fun_file}!')
        except Exception:
            tb = traceback.format_exc()
            errmsg = f'Failed to load modules.{fun_file}: \n{tb}'
            Logger.error(errmsg)
            err_prompt.append(errmsg)
            err_modules.append(fun_file)
    loadercache = os.path.abspath(PrivateAssets.path + '/.cache_loader')
    openloadercache = open(loadercache, 'w')
    if err_prompt:
        err_prompt = re.sub(r'  File \"<frozen importlib.*?>\", .*?\n', '', '\n'.join(err_prompt))
        openloadercache.write(err_prompt)
    else:
        openloadercache.write('')
    openloadercache.close()

    ModulesManager.refresh_modules_aliases()


class ModulesManager:
    modules: Dict[str, Module] = {}
    modules_aliases: Dict[str, str] = {}
    modules_origin: Dict[str, str] = {}

    @classmethod
    def add_module(cls, module: Module, py_module_name: str):
        if module.bind_prefix not in ModulesManager.modules:
            cls.modules.update({module.bind_prefix: module})
            cls.modules_origin.update({module.bind_prefix: py_module_name})
        else:
            raise ValueError(f'Duplicate bind prefix "{module.bind_prefix}"')

    @classmethod
    def remove_modules(cls, modules):
        for module in modules:
            if module in cls.modules:
                Logger.info(f'Removing...{module}')
                cls.modules.pop(module)
                cls.modules_origin.pop(module)
            else:
                raise ValueError(f'Module "{module}" is not exist')

    @classmethod
    def refresh_modules_aliases(cls):
        cls.modules_aliases.clear()
        for m in cls.modules:
            module = cls.modules[m]
            if module.alias:
                cls.modules_aliases.update(module.alias)

    @classmethod
    def search_related_module(cls, module, includeSelf=True):
        if module in cls.modules_origin:
            modules = []
            py_module = cls.return_py_module(module)
            for m in cls.modules_origin:
                if cls.modules_origin[m].startswith(py_module):
                    modules.append(m)
            if not includeSelf:
                modules.remove(module)
            return modules
        else:
            raise ValueError(f'Could not find "{module}" in modules_origin dict')

    @classmethod
    def return_py_module(cls, module):
        if module in cls.modules_origin:
            return re.match(r'^modules(\.[a-zA-Z0-9_]*)?', cls.modules_origin[module]).group()
        else:
            return None

    @classmethod
    def bind_to_module(cls, bind_prefix: str, meta: Union[CommandMeta, RegexMeta, ScheduleMeta, TaskMeta]):
        if bind_prefix in cls.modules:
            if isinstance(meta, CommandMeta):
                cls.modules[bind_prefix].command_list.add(meta)
            elif isinstance(meta, RegexMeta):
                cls.modules[bind_prefix].regex_list.add(meta)
            elif isinstance(meta, ScheduleMeta):
                cls.modules[bind_prefix].schedule_list.add(meta)

    _return_cache = {}

    @classmethod
    def return_modules_list(cls, targetFrom: str = None) -> \
            Dict[str, Module]:
        if targetFrom is not None:
            if targetFrom in cls._return_cache:
                return cls._return_cache[targetFrom]
            returns = {}
            for m in cls.modules:
                if isinstance(cls.modules[m], Module):
                    if targetFrom in cls.modules[m].exclude_from:
                        continue
                    available = cls.modules[m].available_for
                    if targetFrom in available or '*' in available:
                        returns.update({m: cls.modules[m]})
            cls._return_cache.update({targetFrom: returns})
            return returns
        return cls.modules

    @classmethod
    def reload_module(cls, module_name: str):
        """
        重载该小可模块（以及该模块所在文件的其它模块）
        """
        py_module = cls.return_py_module(module_name)
        unbind_modules = cls.search_related_module(module_name)
        cls.remove_modules(unbind_modules)
        cls._return_cache.clear()
        return cls.reload_py_module(py_module)

    @classmethod
    def load_module(cls, module_name: str):
        """
        加载该小可模块（以及该模块所在文件的其它模块）
        """
        if module_name not in current_unloaded_modules:
            return False
        modules = 'modules.' + module_name
        if modules in sys.modules:
            cls.reload_py_module(modules)
            current_unloaded_modules.remove(module_name)
        else:
            try:
                importlib.import_module(modules)
                Logger.info(f'Succeeded loaded modules.{module_name}!')
                if module_name in err_modules:
                    err_modules.remove(module_name)
                current_unloaded_modules.remove(module_name)
            except Exception:
                tb = traceback.format_exc()
                errmsg = f'Failed to load modules.{module_name}: \n{tb}'
                Logger.error(errmsg)
                if module_name not in err_modules:
                    err_modules.append(module_name)
                return False
        cls._return_cache.clear()
        cls.refresh_modules_aliases()
        return True

    @classmethod
    def unload_module(cls, module_name: str):
        """
        卸载该小可模块（以及该模块所在文件的其它模块）
        """
        origin_module = cls.modules_origin[module_name]
        unbind_modules = cls.search_related_module(module_name)
        cls.remove_modules(unbind_modules)
        cls._return_cache.clear()
        cls.refresh_modules_aliases()
        current_unloaded_modules.append(module_name)
        return True

    @classmethod
    def reload_py_module(cls, module_name: str):
        """
        重载该py模块
        """
        try:
            Logger.info(f'Reloading {module_name} ...')
            module = sys.modules[module_name]
            cnt = 0
            loadedModList = list(sys.modules.keys())
            for mod in loadedModList:
                if mod.startswith(f'{module_name}.'):
                    cnt += cls.reload_py_module(mod)
            importlib.reload(module)
            Logger.info(f'Succeeded reloaded {module_name}')
            if (m := re.match(r'^modules(\.[a-zA-Z0-9_]*)?', module_name)) and m.group(1) in err_modules:
                err_modules.remove(m.group(1))
            return cnt + 1
        except BaseException:
            tb = traceback.format_exc()
            errmsg = f'Failed to reload {module_name}: \n{tb}'
            Logger.error(errmsg)
            if (m := re.match(r'^modules(\.[a-zA-Z0-9_]*)?', module_name)) and m.group(1) not in err_modules:
                err_modules.append(m.group(1))
            return -999
        finally:
            cls.refresh_modules_aliases()
