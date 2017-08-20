from .util import *
from functools import partial
import sublime_plugin, sublime, re, os, sys, shutil

cache = {}

def plugin_loaded():
    global cache

    cache_dir = os.path.join(sublime.cache_path(), GLOBAL_SET['package_name'])
    cache['libs'] = DataCache([get_erl_lib_dir()], 'libs', cache_dir)
    cache['libs'].build_data_async()

    all_folders = sublime.active_window().folders()
    project_folder = get_settings_param('erlang_project_folder', all_folders)
    cache['project'] = DataCache(project_folder, 'project', cache_dir)
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

class SaveFileRebuildListener(sublime_plugin.EventListener):
    def on_post_save(self, view):
        caret = view.sel()[0].a

        if not ('source.erlang' in view.scope_name(caret)): 
            return

        cache['project'].build_data_async()

class CompletionsListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):

        if cache['libs'].libs == {}: 
            return

        if not view.match_selector(locations[0], "source.erlang"): 
            return []

        pt = locations[0] - len(prefix) - 1
        ch = view.substr(sublime.Region(pt, pt + 1))

        if ch == ':':
            module_name = view.substr(view.word(pt))
            if module_name.strip() == ':': 
                return

            flag = sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

            if module_name in cache['libs'].libs:
                return (cache['libs'].libs[module_name], flag)

            if module_name in cache['project'].libs:
                return (cache['project'].libs[module_name], flag)

class GotoCommand(sublime_plugin.TextCommand, DataCache):
    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        DataCache.__init__(self)
        self.window = sublime.active_window()

    def run(self, edit):
        line_str = self.get_line_str(self.view)

        math = self.re_dict['take_mf'].search(line_str)
        if math is not None and (len(math.groups()) == 2):
            module_name = math.group(1)
            fun_name = math.group(2)

            key = (module_name, fun_name)
            if key in cache['libs'].fun_postion:
                self.__window_quick_panel_open_window(cache['libs'].fun_postion[key])
            elif key in cache['project'].fun_postion:
                self.__window_quick_panel_open_window(cache['project'].fun_postion[key])

            return

        math = self.re_dict['take_fun'].search(line_str)
        if math is not None and (len(math.groups()) == 1):
            fun_name = math.group(1)

            libs_key = ('erlang', fun_name)
            cur_module = self.get_module_from_path(self.view.file_name())
            project_key = (cur_module, fun_name)
            if libs_key in cache['libs'].fun_postion:
                self.__window_quick_panel_open_window(cache['libs'].fun_postion[libs_key])
            elif project_key in cache['project'].fun_postion:
                self.__window_quick_panel_open_window(cache['project'].fun_postion[project_key])

    def get_line_str(self, view):
        location = view.sel()[0].begin()
        line_region = view.line(location)
        line_str = view.substr(line_region)

        return line_str

    def _jump_to_in_window(self, index, line_number=None, param_cnt=None, transient=0):

        try:
            if self.view.sel()[0] != self.point:
                self.view.sel().clear()
                self.view.sel().add(self.point)
        except AttributeError:
            pass

        if isinstance(index, int):
            if index == -1:  
                self.window.focus_view(self.view)
                self.view.show(self.point)
                return

        (fun_name, filename, line_number) = self.options[index]
        self.window.open_file('{0}:{1}'.format(filename, line_number or 0), sublime.ENCODED_POSITION|transient)

    def __window_quick_panel_open_window(self, options):
        self.point = self.view.sel()[0]
        self.options = options

        self.window.show_quick_panel(
            [self.__show_option(o) for o in options],
            self._jump_to_in_window,
            on_highlight=partial(self._jump_to_in_window, transient=sublime.TRANSIENT))

    def __show_option(self, options):
        return '{1}:{0} line: {2}'.format(*options)