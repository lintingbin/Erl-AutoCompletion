from .util import *
from functools import partial
import sublime_plugin, sublime, re, os, sys, shutil

cache = {}
go_to = None

def plugin_loaded():
    global cache
    global go_to

    cache_dir = os.path.join(sublime.cache_path(), GLOBAL_SET['package_name'])
    cache['libs'] = DataCache([get_erl_lib_dir()], 'libs', cache_dir)
    cache['libs'].build_data_async()

    all_folders = sublime.active_window().folders()
    project_folder = get_settings_param('erlang_project_folder', all_folders)
    cache['project'] = DataCache(project_folder, 'project', cache_dir)
    cache['project'].build_data_async()

    go_to = GoTo()

def plugin_unloaded():
    from package_control import events

    package_name = GLOBAL_SET['package_name']
    if events.remove(package_name):
        print('remove {0}'.format(package_name))
        cache_dir = os.path.join(sublime.cache_path(), package_name)
        shutil.rmtree(cache_dir)

if sys.version_info < (3,):
    plugin_loaded()
    unload_handler = plugin_unloaded

class ErlListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.erlang"): 
            return []

        point = locations[0] - len(prefix) - 1
        letter = view.substr(point)

        if letter == ':':
            module_name = view.substr(view.word(point))
            if module_name.strip() == ':': 
                return

            flag = sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
            completion = cache['libs'].query_mod_fun(module_name)
            if completion != []:
                return (completion, flag)
            completion = cache['project'].query_mod_fun(module_name)
            if completion != []:
                return (completion, flag)
        else:
            if letter == '-' and view.substr(view.line(point))[0] == '-':
                return GLOBAL_SET['-key']

            if re.match('^[0-9a-z_]+$', prefix) and len(prefix) > 1:
                return cache['libs'].query_all_mod() + cache['project'].query_all_mod() + cache['project'].query_mod_fun('erlang')
            
            return ([], sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def on_text_command(self, view, command_name, args):
        if command_name == 'goto' and 'event' in args:
            event = args['event']
            point = view.window_to_text((event['x'], event['y']))

            if not view.match_selector(point, "source.erlang"): 
                return

            go_to.run(point, view, cache)

    def on_post_save(self, view):
        caret = view.sel()[0].a

        if not ('source.erlang' in view.scope_name(caret)): 
            return

        # cache['project'].build_data_async()

class GotoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        return