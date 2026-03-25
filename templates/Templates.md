# Template project

This directory contains a simple working C++ project with examples of how
`eol_scons` is used with SCons.

The `eol_scons` directory must be on the SCons search path to run `scons` in
this project.  One way to do that is to add it directly on the `scons` command
line, assuming this project is contained in a directory named `eol_scons`:

```sh
scons --site-dir=../..
```

Or it can be added to the Python search path:

```sh
export PYTHONPATH=$(realpath ../..)
```

**[SConstruct](SConstruct)** - The top-level SConstruct file.  It imports the
`eol_scons` package, adds some global settings, then configures the build
environment with dependency tools to build a simple program called `interp`.

**[interpolate/SConscript](interpolate/SConscript)** - The SConscript file for
the `interpolate` library.  The top-level SConstruct loads this SConscript
file directly.  The `interpolate` library in turn requires the `vector`
library.

**[vector/tool_vector.py](vector/tool_vector.py)** - The `vector` tool file
builds the `vector` library and also provides a tool which can be used to add
the `vector` library to the `LIBS` dependencies.  This tool file does not need
to be loaded explicitly with a SConscript call (although it could be), because
it is found automatically by `eol_scons` whenever another `Environment`
requires a tool named `vector`.

The top-level SConstruct adds the basic help configuration, and the effect of
that can be seen by running `scons` commands like the following:

```sh
scons -h
scons -h --help-all
scons -h --list-aliases
scons -h --list-defaults
```

In a very large and complicated project, it can be helpful to see what aliases
have been defined to build specific subsets of the project, or what targets
are built by default, especially when an expected target is not being built.

The `-Q` option can be used to suppress some of the messages from `eol_scons`:

```sh
scons -Q .
```

Since the `buildmode` tool is applied by the project's global tool, the
`buildmode` variable can be used to add compile flags to the entire project.
This command shows the effect of enabling all supported compiler flags:

```sh
scons buildmode=debug,optimize,warnings,errors
```

Those settings and other variables can also be added to the `config.py` file
in the same directory as the `SConstruct` file, but the settings require
quotes, like below:

```sh
buildmode="debug,optimize,warnings,errors"
```

The `scons -h --help-all` command shows the current settings of all variables,
whether they are set on the command-line or in a config file, so it can be
helpful to show whether the variables are being set as expected.
