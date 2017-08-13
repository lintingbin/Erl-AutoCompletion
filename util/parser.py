from atexit import register
import os, fnmatch, re, pickle, threading, sublime

class Parser():
    def __init__(self, lib_dir):
        self.lib_dir = lib_dir
        self.libs = {}
        self.fun_postion = {}
        self.modules = []
        self.save_dir = os.path.join(sublime.cache_path(), 'sublime_erl') 
        self.re_dict = {
            'comment' : re.compile(r'%.*\n'),
            'export' : re.compile(r'^\s*-\s*export\s*\(\s*\[\s*([^\]]*)\s*\]\s*\)\s*.', re.DOTALL + re.MULTILINE),
            'funname' : re.compile(r'[a-zA-Z]+\w*\s*\/\s*[0-9]+'),
            'funline' : re.compile(r'\s*((\w+)\s*\(([^)]*)\)).*\-\>'),
            'special_param': re.compile(r'(?:\{.*\})|(?:<<.*>>)|(?:\[.*\])'),
            '=' : re.compile(r'\s*=\s*\w+')
        }

    def __tran2compeletion(self, funname, params, len):
        param_list = ['${%s:%s}' % (i + 1, params[i]) for i in range(len)]
        param_str = ', '.join(param_list)
        completion = '%s(%s) $%s' % (funname, param_str, len + 1)
        return completion

    def build_module_dict(self, filepath):
        with open(filepath, encoding = 'UTF-8') as fd:
            content = fd.read()
            code = re.sub(self.re_dict['comment'], '\n', content)

            all_export_fun = {}
            for export_match in self.re_dict['export'].finditer(code):
                for funname_match in self.re_dict['funname'].finditer(export_match.group()):
                    [name, cnt] = funname_match.group().split('/')
                    all_export_fun[(name, int(cnt))] = None


            (path, filename) = os.path.split(filepath)
            (modname, extension) = os.path.splitext(filename)

            line_cnt = 1
            self.libs[modname] = []
            funline_re = self.re_dict['funline']
            for line in code.split('\n'):
                funhead = funline_re.search(line)
                if funhead is not None: 
                    param_str = re.sub(self.re_dict['special_param'], 'Param', funhead.group(3))
                    param_str = re.sub(self.re_dict['='], '', param_str)
                    funparam = re.split(',\s*', param_str)
                    param_len = len(funparam)
                    if param_str == '' or re.match('\s+', param_str):
                        param_len = 0
                    else:
                        param_len = len(funparam)
                    key = (funhead.group(2), param_len)
                    if key in all_export_fun:
                        del(all_export_fun[key])
                        completion = self.__tran2compeletion(funhead.group(2), funparam, param_len)
                        self.libs[modname].append(('%s/%s\tfunction'% key, completion))
                        self.fun_postion[(modname, funhead.group(2), param_len)] = '%s:%s' % (filepath, line_cnt)
                line_cnt += 1
            self.modules.append(('{0}\tmodule'.format(modname), modname))

    def load_var(self, filename):
        filepath = os.path.join(self.save_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as fd:
                return pickle.load(fd)
        else:
            return None

    def save_var(self, filename, data):
        if not os.path.exists(self.save_dir): 
            os.makedirs(self.save_dir)
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'wb') as fd:
            pickle.dump(data, fd)

    def build_completion(self):
        all_filepath = []
        for root, dirs, files in os.walk(self.lib_dir):
            for file in fnmatch.filter(files, '*.erl'):
                all_filepath.append(os.path.join(root, file))

        save_filepaths = self.load_var('filepaths')
        if save_filepaths is None or save_filepaths != all_filepath:
            for filepath in all_filepath:
                self.build_module_dict(filepath)
            if 'erlang' in self.libs:
                self.modules.extend(self.libs['erlang'])
            self.save_var('filepaths', all_filepath)
            self.save_var('completion', (self.libs, self.modules, self.fun_postion))
        else:
            (self.libs, self.modules, self.fun_postion) = self.load_var('completion')

    def build_completion_async(self):
        this = self
        class BuildCompletionAsync(threading.Thread):
            def run(self):
                this.build_completion()
                
        BuildCompletionAsync().start()