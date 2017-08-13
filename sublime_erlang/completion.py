import sublime, sublime_plugin, os
from .data_cache import CACHE

class CompletionsListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):

        if CACHE['libs'].libs == {}: 
            return

        if not view.match_selector(locations[0], "source.erlang"): 
            return []

        pt = locations[0] - len(prefix) - 1
        ch = view.substr(sublime.Region(pt, pt + 1))

        if ch == ':':
            module_name = view.substr(view.word(pt))
            if module_name.strip() == ':': 
                return

            flag = sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

            if module_name in CACHE['libs'].libs:
                return (CACHE['libs'].libs[module_name], flag)

            if module_name in CACHE['project'].libs:
                return (CACHE['project'].libs[module_name], flag)
                
        else:
            return CACHE['libs'].modules + CACHE['project'].modules