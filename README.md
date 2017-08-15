# Sublime-Erlang

Installation
------------

#### with Git

    cd ~/.config/sublime-text/Packages/ (open by: Preferences->Browse Packages)
    git clone https://github.com/lintingbin2009/Sublime-Erlang
    restart sublime-text

Requirement
--------

Need to install Erlang. If Erlang is not installed, Sublime-Erlang will not be able to create an auto completion and goto definition index based on the version of Erlang you have installed.

Settings
--------

Settings file open by: Preferences -> Package Settings -> Sublime-Erlang

#### escript settings 

If you have set the escript environment variable, you do not need to set the escript value in the configuration file, comment it out.

#### erlang_project_folder settings

This configuration item is used to set the folder where you want to add the source code for the auto completion function.

If you comment out this configuration, you will read all the files that have been opened by Sublime as the value for this configuration item.

Discussing
----
- [Submit issue](https://github.com/lintingbin2009/Erl-AutoCompletion/issues)
- Email: lintingbin31@gmail.com
