import os, fnmatch, re

def get_erl_lib_dir():
    escript = os.popen('where escript').read()
    lib_dir = os.popen('escript get_erl_libs.erl lib_dir').read()
    return lib_dir

lib_dir = get_erl_lib_dir()

get_file = False
for root, dirs, files in os.walk(lib_dir):
    for file in fnmatch.filter(files, '*.erl'):
        filepath = os.path.join(root, file)
        get_file = True
        print(filepath)
        break
    if get_file: 
        break

with open(filepath) as fd:
    content = fd.read()
    code = re.sub(re.compile(r"%.*\n"), '\n', content)
    exports = re.compile(r'^\s*-\s*export\s*\(\s*\[\s*([^\]]*)\s*\]\s*\)\s*.', re.DOTALL + re.MULTILINE)
    funs = re.compile(r'[a-zA-Z]+[a-zA-Z0-9_]*\s*\/\s*[0-9]+')
    for export in exports.findall(code):
        funname = funs.findall(export)
    cur_line = 1
    fun_line = re.compile(r'\s*([a-zA-Z0-9_]+\s*\(.*\))\s*\-\>')
    for line in code.split('\n'):
        fun_line_content = fun_line.findall(line)
        if fun_line_content != []:
            print(fun_line_content, cur_line)
        cur_line += 1
