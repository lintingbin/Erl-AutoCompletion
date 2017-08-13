import sublime_plugin, sublime, re
from . import completion as cp

class GotoDefinitionCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        active_window = sublime.active_window()
        active_view = active_window.active_view()
        location = active_view.sel()[0].begin()
        line_region = active_view.line(location)
        line_str = active_view.substr(line_region)

        math = re.search(r'(\w+)\s*:\s*(\w+)\s*\(([^)]*)\)', line_str)
        if math is not None and (len(math.groups()) == 3):
            param_str = re.sub(r'(?:\{.*\})|(?:<<.*>>)|(?:\[.*\])', 'Param', math.group(3))
            param_str = re.sub(r'\s*=\s*\w+', '', param_str)
            funparam = re.split(',\s*', param_str)
            param_len = len(funparam)
            if param_str == '' or re.match('\s+', param_str):
                param_len = 0
            else:
                param_len = len(funparam)

            key = (math.group(1), math.group(2), param_len)
            if key in cp.parser.fun_postion:
                print(cp.parser.fun_postion[key])
                active_window.open_file(cp.parser.fun_postion[key], sublime.ENCODED_POSITION)