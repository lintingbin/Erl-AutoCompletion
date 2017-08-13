import sublime_plugin, sublime, re
from .data_cache import DataCache, CACHE

class GotoCommand(sublime_plugin.TextCommand, DataCache):
    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        DataCache.__init__(self)

    def run(self, edit):
        window = sublime.active_window()
        line_str = self.get_line_str(self.view)

        math = self.re_dict['take_mf'].search(line_str)
        if math is not None and (len(math.groups()) == 3):
            module_name = math.group(1)
            fun_name = math.group(2)
            param_str = math.group(3)

            param_list = self.format_param(param_str)
            key = (module_name, fun_name, len(param_list))
            if key in CACHE['libs'].fun_postion:
                window.open_file(CACHE['libs'].fun_postion[key], sublime.ENCODED_POSITION)
            elif key in CACHE['project'].fun_postion:
                window.open_file(CACHE['project'].fun_postion[key], sublime.ENCODED_POSITION)

    def get_line_str(self, view):
        location = view.sel()[0].begin()
        line_region = view.line(location)
        line_str = view.substr(line_region)

        return line_str