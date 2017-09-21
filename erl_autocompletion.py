from .util import *
from functools import partial
import sublime_plugin, sublime, re, os, sys, shutil

cache = {}

def plugin_loaded():
    global cache

    cache_dir = os.path.join(sublime.cache_path(), GLOBAL_SET['package_name'])
    cache['libs'] = DataCache('libs', cache_dir, [get_erl_lib_dir()])
    cache['libs'].build_data_async()

    cache['project'] = DataCache('project', cache_dir)
    cache['project'].build_data_async()

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
                return cache['libs'].query_all_mod() + cache['project'].query_all_mod() + cache['libs'].query_mod_fun('erlang')
            
            return ([], sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def on_text_command(self, view, command_name, args):
        if command_name == 'goto' and 'event' in args:
            event = args['event']
            point = view.window_to_text((event['x'], event['y']))

            if not view.match_selector(point, "source.erlang"): 
                return

            go_to = GoTo()
            go_to.run(point, view, cache, is_quick_panel = True)

    def on_hover(self, view, point, hover_zone):
        if not view.match_selector(point, "source.erlang"): 
            return

        go_to = GoTo()
        go_to.run(point, view, cache)

    def on_post_save_async(self, view):
        caret = view.sel()[0].a

        if not ('source.erlang' in view.scope_name(caret)): 
            return

        cache['project'].rebuild_module_index(view.file_name())

    def on_window_command(self, window, command_name, args):
        if command_name == 'remove_folder':
            cache['project'].delete_module_index(args['dirs'])

    def on_load(self, view):
        cache['project'].build_data_async()

class GotoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        return