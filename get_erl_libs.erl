#!/usr/bin/env escript

-mode(compile).

% command line exposure
main(["lib_dir"]) ->
  io:format("~s", [code:lib_dir()]);
main(_) ->
  halt(1).