import sublime, re, os

def get_plugin_settings():
    setting_name = 'sublime_erlang.sublime-settings'
    plugin_settings = sublime.load_settings(setting_name)
    return plugin_settings


def get_settings_param(param_name, default=None):
    plugin_settings = get_plugin_settings()
    project_settings = sublime.active_window().active_view().settings()
    return project_settings.get(
        param_name,
        plugin_settings.get(param_name, default)
    )

def get_erl_lib_dir():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    escript = get_settings_param('escript', 'escript')
    lib_dir = os.popen('{0} get_erl_libs.erl lib_dir'.format(escript)).read()
    return lib_dir

GLOBAL_SET = {
    'compiled_re' : {
        'comment' : re.compile(r'%.*\n'),
        'export' : re.compile(r'^\s*-\s*export\s*\(\s*\[\s*([^\]]*)\s*\]\s*\)\s*.', re.DOTALL + re.MULTILINE),
        'funname' : re.compile(r'[a-zA-Z]+\w*\s*\/\s*[0-9]+'),
        'funline' : re.compile(r'\s*(\w+)\s*\(([^)]*)\).*\-\>'),
        'special_param': re.compile(r'(?:\{.*\})|(?:<<.*>>)|(?:\[.*\])'),
        '=' : re.compile(r'\s*=\s*\w+'),
        'take_mf' : re.compile(r'(\w+)\s*:\s*(\w+)\s*\('),
        'take_fun' : re.compile(r'(\w+)\s*\(')
    },
    'package_name' : 'Erl-AutoCompletion'
}