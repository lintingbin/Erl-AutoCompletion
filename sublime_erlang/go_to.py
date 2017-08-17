import sublime_plugin, sublime, re
from .data_cache import DataCache, CACHE
from functools import partial

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
            if key in CACHE['libs'].fun_postion:
                self.__window_quick_panel_open_window(CACHE['libs'].fun_postion[key])
            elif key in CACHE['project'].fun_postion:
                self.__window_quick_panel_open_window(CACHE['project'].fun_postion[key])

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