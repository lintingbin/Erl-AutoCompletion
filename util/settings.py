import sublime, re, os

def get_plugin_settings():
    setting_name = 'erl_autocompletion.sublime-settings'
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
        'take_fun' : re.compile(r'(\w+)\s*[\(|/]'),
        'take_record' : re.compile(r'\#\s*(\w+)\s*[\{|.]'),
        'take_define' : re.compile(r'\?\s*(\w+)'),
        'take_include' : re.compile(r'-include\("([^\)]*)"\)')
    },
    'package_name' : 'Erl-AutoCompletion',
    '-key' : [
        ["-behaviour\tDirectives", "-behaviour(${1:behaviour})."],
        ["-callback\tDirectives", "-callback ${1:function}(${2:Parameters}) -> ${3:ReturnType}."],
        ["-compile\tDirectives", "-compile([${1:export_all}])."],
        ["-define\tDirectives", "-define(${1:macro}, ${2:value})."],
        ["-else\tDirectives", "-else."],
        ["-endif\tDirectives", "-endif."],
        ["-export\tDirectives", "-export([${1:function}/${2:arity}])."],
        ["-export_type\tDirectives", "-export_type([${1:type}/${2:arity}])."],
        ["-ifdef\tDirectives", "-ifdef(${1:macro})."],
        ["-ifndef\tDirectives", "-ifndef(${1:macro})."],
        ["-import\tDirectives", "-import(${1:module}, [${2:function}/${3:arity}])."],
        ["-include\tDirectives", "-include(\"${1:file.hrl}\")."],
        ["-include_lib\tDirectives", "-include_lib(\"${1:app/file.hrl}\")."],
        ["-module\tDirectives", "-module(${1:${TM_FILEPATH/^.*\\/(.*)\\.[a-z]+$/$1/g}})."],
        ["-opaque\tDirectives", "-opaque ${1:type}() :: ${2:term()}."],
        ["-record\tDirectives", "-record(${1:record, {${2:field}${3: = ${4:value}}}})."],
        ["-spec\tDirectives", "-spec ${1:function}(${2:Parameters}) -> ${3:ReturnType}."],
        ["-type\tDirectives", "-type ${1:type}() :: ${2:term()}."],
        ["-undef\tDirectives", "-undef(${1:macro})."]
    ]
}