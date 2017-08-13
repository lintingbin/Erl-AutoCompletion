import os, fnmatch, re, pickle, gzip, threading, sublime
from .settings import get_erl_lib_dir, get_settings_param, GLOBAL_SET

CACHE = {}

def plugin_loaded():
    global CACHE
    CACHE['libs'] = DataCache([get_erl_lib_dir()], 'libs')
    CACHE['libs'].build_data_async()

    default_project = sublime.active_window().folders()
    project_folder = get_settings_param('erlang_project_folder', default_project)
    CACHE['project'] = DataCache(project_folder, 'project')
    CACHE['project'].build_data_async()

class DataCache:
    def __init__(self, dir = '', data_type = ''):
        self.dir = dir
        self.libs = {}
        self.fun_postion = {}
        self.modules = []
        self.data_type = data_type;
        self.cache_dir = GLOBAL_SET['cache_dir']
        self.re_dict = GLOBAL_SET['compiled_re']
        self.version = get_settings_param('sublime_erlang_version', '0.0.0')

    def build_module_dict(self, filepath):
        with open(filepath, encoding = 'UTF-8', errors='ignore') as fd:
            content = fd.read()
            code = re.sub(self.re_dict['comment'], '\n', content)

            export_fun = {}
            for export_match in self.re_dict['export'].finditer(code):
                for funname_match in self.re_dict['funname'].finditer(export_match.group()):
                    [name, cnt] = funname_match.group().split('/')
                    export_fun[(name, int(cnt))] = None

            (path, filename) = os.path.split(filepath)
            (module, extension) = os.path.splitext(filename)

            row_id = 1
            self.libs[module] = []
            for line in code.split('\n'):
                funhead = self.re_dict['funline'].search(line)
                if funhead is not None: 
                    fun_name = funhead.group(1)
                    param_str = funhead.group(2)
                    param_list = self.format_param(param_str)
                    param_len = len(param_list)
                    if (fun_name, param_len) in export_fun:
                        del(export_fun[(fun_name, param_len)])
                        completion = self.__tran2compeletion(fun_name, param_list, param_len)
                        self.libs[module].append(('{0}/{1}\tfunction'.format(fun_name, param_len), completion))
                        self.fun_postion[(module, fun_name, param_len)] = '{0}:{1}'.format(filepath, row_id)
                row_id += 1
            self.modules.append(('{0}\tmodule'.format(module), module))

    def format_param(self, param_str):
        param_str = re.sub(self.re_dict['special_param'], 'Param', param_str)
        param_str = re.sub(self.re_dict['='], '', param_str)

        if param_str == '' or re.match('\s+', param_str):
            return []
        else:
            return re.split(',\s*', param_str)

    def __tran2compeletion(self, funname, params, len):
        param_list = ['${{{0}:{1}}}'.format(i + 1, params[i]) for i in range(len)]
        param_str = ', '.join(param_list)
        completion = '{0}({1})${2}'.format(funname, param_str, len + 1)
        return completion

    def __get_filepath(self, filename):
        if not os.path.exists(self.cache_dir): 
            os.makedirs(self.cache_dir)
        real_filename = '{0}_{1}'.format(self.data_type, filename)
        filepath = os.path.join(self.cache_dir, real_filename)
        return filepath

    def __load_data(self, filename):
        filepath = self.__get_filepath(filename)
        if os.path.exists(filepath):
            with gzip.open(filepath, 'rb') as fd:
                return pickle.load(fd)
        else:
            return None

    def __save_data(self, filename, data):
        filepath = self.__get_filepath(filename)
        with gzip.open(filepath, 'wb') as fd:
            pickle.dump(data, fd)

    def build_data(self):
        all_filepath = []
        for dir in self.dir:
            for root, dirs, files in os.walk(dir):
                for file in fnmatch.filter(files, '*.erl'):
                    all_filepath.append(os.path.join(root, file))

        if all_filepath == []:
            (self.libs, self.modules, self.fun_postion) = self.__load_data('completion')
        else:
            cache_info = self.__load_data('cache_info')
            new_cache_info = (self.version, all_filepath)
            if cache_info is None or cache_info != new_cache_info:
                for filepath in all_filepath:
                    self.build_module_dict(filepath)
                if 'erlang' in self.libs:
                    self.modules.extend(self.libs['erlang'])
                self.__save_data('cache_info', new_cache_info)
                self.__save_data('completion', (self.libs, self.modules, self.fun_postion))
            else:
                (self.libs, self.modules, self.fun_postion) = self.__load_data('completion')

    def build_data_async(self):
        this = self
        class BuildDataAsync(threading.Thread):
            def run(self):
                this.build_data()
                
        BuildDataAsync().start()