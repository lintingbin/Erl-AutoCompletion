import os, fnmatch, re, threading, sublime, sqlite3, shutil, time
from multiprocessing.pool import ThreadPool
from .settings import get_settings_param, GLOBAL_SET

CREATE_LIBS_INFO_SQL = '''
create table if not exists libs_info (
    id int unsigned not null,
    parent_id int unsigned not null,
    folder varchar(256) not null,
    primary key(id)
);
'''

INSERT_FOLDER_INFO = '''
replace into libs_info(id, parent_id, folder) values
(?, ?, ?);
'''

QUERY_FOLDER = '''
select id, parent_id from libs_info where folder = ?;
'''

CREATE_LIBS_SQL = '''
create table if not exists libs (
    id int unsigned not null,
    mod_name varchar(128) not null,
    fun_name varchar(128) not null,
    param_len tinyint(2) not null,
    row_num int unsigned not null,
    completion varchar(256) not null,
    primary key(id, mod_name, fun_name, param_len)
); 
'''

INSERT_LIBS_SQL = '''
replace into libs(id, mod_name, fun_name, param_len, row_num, completion) values 
(?, ?, ?, ?, ?, ?);
'''

DEL_LIBS_SQL = '''
delete from libs where id = ? and mod_name = ?;
'''

QUERY_COMPLETION = '''
select fun_name, param_len, completion from libs where mod_name = ?;
'''

QUERY_ALL_MOD = '''
select distinct mod_name from libs;
'''

QUERY_POSITION = '''
select folder, fun_name, param_len, row_num from libs join libs_info where libs_info.id = libs.id and mod_name = ? and fun_name = ?;
'''

DEL_FOLDER_LIBS_SQL = '''
delete from libs where id in (select id from libs_info where parent_id = ?);
'''

DEL_FOLDER_SQL = '''
delete from libs_info where parent_id = ? or folder = ?;
'''
class DataCache:
    def __init__(self, data_type = '', cache_dir = '', dir = None):
        self.dir = dir
        self.data_type = data_type
        self.cache_dir = cache_dir
        self.re_dict = GLOBAL_SET['compiled_re']
        self.pool_size = 8
        self.folder_id = 1
        if cache_dir != '':
            self.__init_db()

    def __init_db(self):
        if os.path.exists(self.cache_dir): 
            shutil.rmtree(self.cache_dir)
        self.db_con = sqlite3.connect(':memory:', check_same_thread = False)
        self.db_cur = self.db_con.cursor()
        self.db_cur.execute(CREATE_LIBS_INFO_SQL)
        self.db_cur.execute(CREATE_LIBS_SQL)

    def query_mod_fun(self, module):
        query_data = []
        try:
            self.lock.acquire(True)
            self.db_cur.execute(QUERY_COMPLETION, (module, ))
            query_data = self.db_cur.fetchall()
        finally:
            self.lock.release()

        completion_data = []
        all_fun = []
        for (fun_name, param_len, param_str) in query_data:
            if (fun_name, param_len) not in all_fun:
                param_list = self.format_param(param_str)
                completion = self.__tran2compeletion(fun_name, param_list, param_len)
                completion_data.append(['{}/{}\tMethod'.format(fun_name, param_len), completion])
                all_fun.append((fun_name, param_len))

        return completion_data

    def query_all_mod(self):
        query_data = []
        try:
            self.lock.acquire(True)
            self.db_cur.execute(QUERY_ALL_MOD)
            query_data = self.db_cur.fetchall()
        finally:
            self.lock.release()

        completion_data = []
        for (mod_name, ) in query_data:
            completion_data.append(['{}\tModule'.format(mod_name), mod_name])

        return completion_data

    def query_fun_position(self, module, function):
        query_data = []
        try:
            self.lock.acquire(True)
            self.db_cur.execute(QUERY_POSITION, (module, function))
            query_data = self.db_cur.fetchall()
        finally:
            self.lock.release()

        completion_data = []
        for (folder, fun_name, param_len, row_num) in query_data:
            filepath = os.path.join(folder, module + '.erl')
            completion_data.append(('{}/{}'.format(fun_name, param_len), filepath, row_num))

        return completion_data

    def build_module_index(self, filepath, folder_id):
        with open(filepath, encoding = 'UTF-8', errors='ignore') as fd:
            content = fd.read()
            code = re.sub(self.re_dict['comment'], '\n', content)

            export_fun = {}
            for export_match in self.re_dict['export'].finditer(code):
                for funname_match in self.re_dict['funname'].finditer(export_match.group()):
                    [name, cnt] = funname_match.group().split('/')
                    export_fun[(name, int(cnt))] = None
            module = self.get_module_from_path(filepath)

            row_num = 1
            for line in code.split('\n'):
                funhead = self.re_dict['funline'].search(line)
                if funhead is not None: 
                    fun_name = funhead.group(1)
                    param_str = funhead.group(2)
                    param_list = self.format_param(param_str)
                    param_len = len(param_list)
                    if (fun_name, param_len) in export_fun:
                        del(export_fun[(fun_name, param_len)])
                        try:
                            self.lock.acquire(True)
                            self.db_cur.execute(INSERT_LIBS_SQL, (folder_id, module, fun_name, param_len, row_num, param_str))
                        finally:
                            self.lock.release()
                row_num += 1

    def get_module_from_path(self, filepath):
        (path, filename) = os.path.split(filepath)
        (module, extension) = os.path.splitext(filename)
        return module

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

    def build_data(self):
        all_filepath = []
        start_time = time.time()
        task_pool = ThreadPool(self.pool_size)
        self.lock = threading.Lock()

        if self.dir == None:
            folders = self.get_all_open_folders()
        else:
            folders = self.dir

        is_save_build_index = False
        for folder in folders:
            if self.get_folder_id(folder) != None:
                continue

            print('build {}: {} index'.format(self.data_type, folder))
            is_save_build_index = True
            self.db_cur.execute(INSERT_FOLDER_INFO, (self.folder_id, 0, folder))
            parent_id = self.folder_id
            for root, dirs, files in os.walk(folder):
                erl_files = fnmatch.filter(files, '*.erl')
                if erl_files == []:
                    continue
                    
                if folder != root:
                    self.folder_id += 1
                    self.db_cur.execute(INSERT_FOLDER_INFO, (self.folder_id, parent_id, root))
                for file in erl_files:
                    all_filepath.append((os.path.join(root, file), self.folder_id))
                self.folder_id += 1
        
        task_pool.starmap(self.build_module_index, all_filepath)
        self.db_con.commit()
        is_save_build_index and print("build {} index, use {} second".format(self.data_type, time.time() - start_time))

    def get_all_open_folders(self):
        all_folders = []
        for window in sublime.windows():
            all_folders = all_folders + window.folders()

        return all_folders

    def get_folder_id(self, folder):
        try:
            self.lock.acquire(True)
            self.db_cur.execute(QUERY_FOLDER, (folder, ))
            for (fid, pid) in self.db_cur.fetchall():
                return (fid, pid)
        finally:
            self.lock.release()
        return None

    def rebuild_module_index(self, filepath):
        (folder, filename) = os.path.split(filepath)
        (module, extension) = os.path.splitext(filename)
        (fid, pid) = self.get_folder_id(folder)
        try:
            self.lock.acquire(True)
            self.db_cur.execute(DEL_LIBS_SQL, (fid, module))
        finally:
            self.lock.release()
        self.build_module_index(filepath, fid)
        self.db_con.commit()

    def delete_module_index(self, folders):
        for folder in folders:
            try:
                self.lock.acquire(True)
                folder_info = self.get_folder_id(folder)
                self.db_cur.execute(DEL_FOLDER_LIBS_SQL, (folder_info[0], ))
                self.db_cur.execute(DEL_FOLDER_SQL, (folder_info[0], folder))
            finally:
                self.lock.release()
        self.db_con.commit()

    def build_data_async(self):
        this = self
        class BuildDataAsync(threading.Thread):
            def run(self):
                this.build_data()
                
        BuildDataAsync().start()