from .data_cache import DataCache
from functools import partial
from html import escape
import sublime, re, os

class GoTo(DataCache):
    def __init__(self):
        DataCache.__init__(self)
        self.__max_col = 400
        self.__line_style = 'margin:5 0'
        self.__definition_style = 'font-weight:bold;font-size:20;margin:5 0'

    def run(self, point, view, cache, is_quick_panel = False):
        self.__view = view
        self.__point = point
        self.__window = view.window()
        self.__is_quick_panel = is_quick_panel

        line_region = view.line(point)
        line_str = view.substr(line_region)
        word_region = view.word(point)
        word = view.substr(word_region)
        filepath = view.file_name()

        maths = self.re_dict['take_mf'].findall(line_str)
        for math in maths:
            if word in math:
                if self.__goto_menu(view, cache['libs'].query_fun_position(math[0], math[1])):
                    return
                if self.__goto_menu(view, cache['project'].query_fun_position(math[0], math[1])):
                    return

        maths = self.re_dict['take_fun'].findall(line_str)
        for math in maths:
            if word == math:
                module = self.get_module_from_path(filepath)
                if self.__goto_menu(view, cache['libs'].query_fun_position('erlang', math)):
                    return
                if self.__goto_menu(view, self.__build_module_position(view, module, math, filepath)):
                    return

        maths = self.re_dict['take_record'].findall(line_str)
        for math in maths:
            if word == math:
                re_define = re.compile(r'(-\s*record\s*\([\s\n\r]*' + word + r'[\s\n\r]*,[\s\n\r]*{[^-]*}[\s\n\r]*\)\.)', re.MULTILINE|re.DOTALL)
                if self.__open_hrl_popup(view, re_define, filepath):
                    return

        maths = self.re_dict['take_define'].findall(line_str)
        for math in maths:
            if word == math:
                re_define = re.compile(r'(-\s*define\s*\([\s\n\r]*' + word + r'[\s\n\r]*,[\s\n\r]*[^-]*\)\.)', re.MULTILINE|re.DOTALL)
                if self.__open_hrl_popup(view, re_define, filepath):
                    return

    def __goto_menu(self, view, data):
        if data == []:
            return False

        if self.__is_quick_panel:
            self.__window_quick_panel_open_window(data)
        else:
            self.__open_function_popup(view, data)
        return True

    def __open_function_popup(self, view, data):
        col = 0
        row = 1
        html_content = '<div style={}>Definitions:</div>'.format(self.__definition_style)
        for (name, path, row) in data:
            add_str = '<div style={0}>{1} <a href="{2}:{3}:0">{2}:{3}</a></div>'.format(self.__line_style, name, path, row)
            html_content += add_str
            col = max(len(add_str), col)
            row += 1

        view.show_popup(html_content, max_height = self.__get_height(row), max_width = self.__get_width(col), 
            flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY, location = self.__point, 
            on_navigate = self.__on_navigate_cb)
        return True

    def __build_module_position(self, view, module, fun, filepath):
        row_num = 1
        cur_view_position = []
        all_cur_view_fun = []
        code = self.__get_view_code(view)
        for line in code.split('\n'):
            funhead = self.re_dict['funline'].search(line)
            if funhead is not None: 
                fun_name = funhead.group(1)
                if fun_name == fun:
                    param_str = funhead.group(2)
                    param_list = self.format_param(param_str)
                    key = (module, fun_name)
                    param_len = len(param_list)
                    format_fun_name = '{0}/{1}'.format(fun_name, param_len)
                    
                    if (key, param_len) not in all_cur_view_fun:
                        cur_view_position.append((format_fun_name, filepath, row_num))
                        all_cur_view_fun.append((key, param_len))
            row_num += 1
        return cur_view_position

    def __open_hrl_popup(self, view, re_define, filepath):
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, encoding = 'UTF-8', errors='ignore') as fd:
            content = fd.read()
            code = re.sub(self.re_dict['comment'], '\n', content)

        re_newline = re.compile(r'\n')
        for m in re_define.finditer(code):
            start_line = len(re_newline.findall(code, 0, m.start(1))) + 1

            if self.__is_quick_panel:
                self.__window_quick_panel_open_window([('', filepath, start_line)])
            else:
                html_content = '<div style={}>Definitions:</div>'.format(self.__definition_style)
                record_define = '<div style={}>{}</div>'.format(self.__line_style, escape(m.group(1), quote = False))
                record_address = '<div style={0}><a href="{1}:{2}:0">{1}:{2}</a></div>'.format(self.__line_style, filepath, start_line)
                record_define_len = len(record_define)
                if record_define_len > self.__max_col:
                    html_content += record_address
                    col = len(record_address)
                else:
                    html_content += record_define + record_address
                    col = max(record_define_len, len(record_address))

                view.show_popup(html_content, max_height = self.__get_height(3), max_width = self.__get_width(col), 
                    flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY, location = self.__point, 
                    on_navigate = self.__on_navigate_cb)
            return True
        
        (directory, filename) = os.path.split(filepath)
        for m in self.re_dict['take_include'].finditer(code):
            hrl_name = m.group(1)
            hrl_path = os.path.normpath(os.path.join(directory, hrl_name))
            if self.__open_hrl_popup(view, re_define, hrl_path):
                return True
                
        return False

    def __on_navigate_cb(self, address):
        sublime.active_window().open_file(address, sublime.ENCODED_POSITION)

    def __get_view_code(self, view):
        view_region = sublime.Region(0, view.size())
        code = view.substr(view_region)
        return code

    def __window_quick_panel_open_window(self, options):
        self.options = options

        self.__window.show_quick_panel(
            [self.__show_option(o) for o in options],
            self.__jump_to_in_window,
            on_highlight=partial(self.__jump_to_in_window))

    def __jump_to_in_window(self, index, row_num = None, param_cnt = None):
        if index == -1:  
            self.__window.focus_view(self.__view)
            self.__view.show(self.__point)
            self.__view.sel().clear()
            self.__view.sel().add(self.__point)
            return

        (fun_name, filepath, row_num) = self.options[index]
        self.__window.open_file('{0}:{1}'.format(filepath, row_num or 0), sublime.ENCODED_POSITION|sublime.TRANSIENT)

    def __show_option(self, options):
        return '{0}: {1}:{2}'.format(*options)

    def __get_height(self, row):
        return row * 240

    def __get_width(self, col):
        return col * 20
