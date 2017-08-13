import sublime, sublime_plugin, os
from .parser import Parser

def get_erl_lib_dir():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    escript = os.popen('where escript').read()
    lib_dir = os.popen('escript get_erl_libs.erl lib_dir').read()
    return lib_dir

parser = None
lib_dir = get_erl_lib_dir()

def plugin_loaded():
    global parser
    global lib_dir
    parser = Parser(lib_dir)
    parser.build_completion_async()

class CompletionsListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        global parser

        if parser.libs == {}: return

        # only trigger within erlang
        if not view.match_selector(locations[0], "source.erlang"): return []

        # only trigger if : was hit
        pt = locations[0] - len(prefix) - 1
        ch = view.substr(sublime.Region(pt, pt + 1))
        print('prefix {0} location {1}'.format(prefix, locations[0]))

        if ch == ':':
            # get function name that triggered the autocomplete
            module_name = view.substr(view.word(pt))
            if module_name.strip() == ':': return
            print("module name {0}".format(module_name))

            if module_name in parser.libs:
                available_completions = parser.libs[module_name]
            else: 
                return

            # return snippets
            return (available_completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        else:
            return parser.modules