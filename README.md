# Erl-AutoCompletion

This is an Erlang auto-completion and goto-definition plugin of the Sublime editor. It only supports **Sublime Text 3**. If you are using Sublime Text 2, please upgrade to Sublime Text 3.

Installation
------------

#### with [Sublime Package Control](http://wbond.net/sublime_packages/package_control)

 1. Open command pallet (default: `ctrl+shift+p`)
 2. Type `package control install` and select command `Package Control: Install Package`
 3. Type `Erl-AutoCompletion` and select `Erl-AutoCompletion`

Additional info about to use Sublime Package Control you can find here: [http://wbond.net/sublime_packages/package_control/usage](http://wbond.net/sublime_packages/package_control/usage).

#### with Git

    cd ~/.config/sublime-text/Packages/ (open by: Preferences -> Browse Packages)
    git clone https://github.com/lintingbin2009/Erl-AutoCompletion
    restart sublime-text

Goto definition
------------

The right mouse button can bring up the goto_definition(Erlang) menu. It can find definition of function, record and macro. You can set mousemap by Preferences -> Package Settings -> Erl-AutoCompletion -> Mousemap - default.

Requirement
--------

Need to install Erlang. If Erlang is not installed, Erl-AutoCompletion will not be able to create an auto completion and goto definition index based on the version of Erlang you have installed.

Settings
--------

Settings file open by: Preferences -> Package Settings -> Erl-AutoCompletion

#### escript settings 

If you have set the escript environment variable, you do not need to set the escript value in the configuration file, comment it out.

#### erlang_project_folder settings

This configuration item is used to set the folder where you want to add the source code for the auto completion and goto definition function.

If you comment out this configuration(default), the plugin will read all the files that have been opened by Sublime as the value for this configuration item.

#### Autocomplete on ":"

If you want auto-completion on ":", you can define a trigger in the
Sublime User or Erlang preferences:

    # User/Preferences.sublime-settings or User/Erlang.sublime-settings
    {
        // ...
        "auto_complete_triggers": [{"selector": "source.erlang", "characters": ":"}],
    }

Discussing
----
- [Submit issue](https://github.com/lintingbin2009/Erl-AutoCompletion/issues)
- Email: lintingbin31@gmail.com
