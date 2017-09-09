from .data_cache import DataCache
import sublime, re, os

class GoTo(DataCache):
    def __init__(self):
        DataCache.__init__(self)
        self.max_col = 400

    def run(self, point, view, cache):
        line_region = view.line(point)
        line_str = view.substr(line_region)
        word_region = view.word(point)
        word = view.substr(word_region)
        filepath = view.file_name()

        maths = self.re_dict['take_mf'].findall(line_str)
        for math in maths:
            if word in math:
                if self.open_function_popup(view, point, math[0], math[1], cache['libs'].fun_position):
                    return
                if self.open_function_popup(view, point, math[0], math[1], cache['project'].fun_position):
                    return

        maths = self.re_dict['take_fun'].findall(line_str)
        for math in maths:
            if word == math:
                module = self.get_module_from_path(filepath)
                if self.open_function_popup(view, point, 'erlang', math, cache['libs'].fun_position):
                    return
                if self.open_function_popup(view, point, module, math, self.build_module_position(view, module, filepath)):
                    return

        maths = self.re_dict['take_record'].findall(line_str)
        for math in maths:
            if word == math:
                re_define = re.compile(r'(-\s*record\s*\([\s\n\r]*' + word + r'[\s\n\r]*,[\s\n\r]*{[^-]*}[\s\n\r]*\)\.)', re.MULTILINE|re.DOTALL)
                if self.open_hrl_popup(view, re_define, filepath, point):
                    return

        maths = self.re_dict['take_define'].findall(line_str)
        for math in maths:
            if word == math:
                re_define = re.compile(r'(-\s*define\s*\([\s\n\r]*' + word + r'[\s\n\r]*,[\s\n\r]*[^-]*\)\.)', re.MULTILINE|re.DOTALL)
                if self.open_hrl_popup(view, re_define, filepath, point):
                    return

    def open_function_popup(self, view, point, module, function, all_function):
        key = (module, function)
        if key in all_function:
            col = 0
            row = 1
            html_content = '<div>Definitions:</div>'
            for (name, path, row) in all_function[key]:
                add_str = '<div>{0}:{1} <a href="{2}:{3}:0">{2}:{3}</a></div>'.format(module, name, path, row)
                html_content += add_str
                col = max(len(add_str), col)
                row += 1

            view.show_popup(html_content, max_height = self.get_height(row), max_width = self.get_width(col), 
                flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY, location = point, 
                on_navigate = self.on_navigate_cb)
            return True
        return False

    def build_module_position(self, view, module, filepath):
        row_id = 1
        cur_view_position = {}
        all_cur_view_fun = []
        code = self.get_view_code(view)
        for line in code.split('\n'):
            funhead = self.re_dict['funline'].search(line)
            if funhead is not None: 
                fun_name = funhead.group(1)
                param_str = funhead.group(2)
                param_list = self.format_param(param_str)
                key = (module, fun_name)
                param_len = len(param_list)
                format_fun_name = '{0}/{1}'.format(fun_name, param_len)
                
                if (key, param_len) not in all_cur_view_fun:
                    if key not in cur_view_position:
                        cur_view_position[key] = []
                    cur_view_position[key].append((format_fun_name, filepath, row_id))
                    all_cur_view_fun.append((key, param_len))
            row_id += 1
        return cur_view_position

    def open_hrl_popup(self, view, re_define, filepath, point):
        with open(filepath, encoding = 'UTF-8', errors='ignore') as fd:
            content = fd.read()
            code = re.sub(self.re_dict['comment'], '\n', content)

        re_newline = re.compile(r'\n')
        for m in re_define.finditer(code):
            start_line = len(re_newline.findall(code, 0, m.start(1))) + 1
            html_content = '<div>Definitions:</div>'
            record_define = '<div>{0}</div>'.format(m.group(1))
            reocrd_address = '<div><a href="{0}:{1}:0">{0}:{1}</a></div>'.format(filepath, start_line)
            record_define_len = len(record_define)
            if record_define_len > self.max_col:
                html_content += reocrd_address
                col = len(reocrd_address)
            else:
                html_content += record_define + reocrd_address
                col = max(record_define_len, len(reocrd_address))

            view.show_popup(html_content, max_height = self.get_height(3), max_width = self.get_width(col), 
                flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY, location = point, 
                on_navigate = self.on_navigate_cb)
            return True
        
        (directory, filename) = os.path.split(filepath)
        for m in self.re_dict['take_include'].finditer(code):
            hrl_name = m.group(1)
            hrl_path = os.path.normpath(os.path.join(directory, hrl_name))
            if self.open_hrl_popup(view, re_define, hrl_path, point):
                return True
                
        return False

    def on_navigate_cb(self, address):
        sublime.active_window().open_file(address, sublime.ENCODED_POSITION)

    def get_view_code(self, view):
        view_region = sublime.Region(0, view.size())
        code = view.substr(view_region)
        return code

    def get_height(self, row):
        return row * 240

    def get_width(self, col):
        return col * 20
