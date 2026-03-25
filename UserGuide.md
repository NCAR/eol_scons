# User Guide for eol_scons

## Overview

This `eol_scons` software configuration package is an extension to
[SCons](https://scons.org) for modularizing and encapsulating the commands and
configuration required to build software. Libraries and executables can be
compiled and shared across the whole tree, without knowing whether
dependencies are internal or external to the tree. Likewise options for
configuring the build can be defined in one place but shared across all
modules which use those options.

The main objective is a modular, flexible, and portable build system. Given
various libraries and executables in the source tree, where each builds
against some subset of the libraries and some subset of external packages, the
build for a program in the source tree should only need to name its required
packages without regard for the location of those packages.  For example, a
program needing the _util_ library specifies _util_ as a package requirement
which causes the proper libraries and include paths to be added to the
environment.  The _util_ library itself may require other libraries, and those
libraries should also be added to the environment automatically.  A program
which builds against the _util_ library should not need to know that the util
library must also link against library _tools_.  Each module is responsible
for publishing (or exporting) the build setup information which other modules
would need to compile and link against that module, thus isolating the build
configuration in each source directory from changes in the location or
configuration of its dependencies.

## Implementation

The implementation is a python package called `eol_scons` and a set of `SCons`
tools which extends the standard `SCons` tools.  Every component within the
source tree as well as external components have a particular tool which
configures a scons `Environment` for building against that component.  The
`eol_scons` package provides a table of global targets that `SConscript` files
throughout the source tree can use to find dependencies, without knowing where
those dependencies are built or installed.  For example, the tool for a
library like `netcdf`, whether installed on the system or built within the
source tree, defines a function for configuring the build environment.
Sometimes the tools are loaded from a tool file from the common
`site_scons/site_tools` directory, sometimes via a Python script named
`tool_{toolname}.py`, and other times the tool is a function defined within
the `SConscript` file which builds the library or dependency.  Either way, the
tools are genuine scons tools, so they can be applied to an `Environment` like
any other tool.  In particular, they can be applied with the `Tool()` method
or passed in the tools list when an `Environment` is constructed.

### Installation

See [README.md](README.md) for installation.

### Activating eol_scons

There are two parts to extending SCons with eol_scons.  The first part is
inserting eol_scons into the scons tool path so that eol_scons can override
some of the standard SCons tools.  This modifies the global SCons state rather
than just one `Environment` instance.  The second part to extending SCons is
the customization of an `Environment` instance.  This is the part that behaves
like a normal scons tool.

Installing eol_scons on the python search path does not automatically activate
it within a SCons session.  The eol_scons tools are not on the default tool
path, and eol_scons does not install a `site_init.py` file.

The first part happens when eol_scons is imported, when it automatically
inserts the eol_scons tools directory into the scons tool path.  It also
inserts a second tools directory containing a
[default.py](eol_scons/hooks/default.py) tool module to override the scons
`default` tool.  By overriding the `default` tool, eol_scons can apply itself
to every `Environment` created by scons to which the `default` tool is
applied, which usually is every `Environment` in a source tree.  This is the
usual way to activate eol_scons in a scons build, since it avoids explicitly
applying eol_scons to every `Environment` constructor call.  To activate
eol_scons this way, import eol_scons at the top of the `SConstruct` file,
before any tools are loaded:

```python
import eol_scons
...
env = Environment(tools=['default'])
```

The overridden default tool first applies the standard scons default tools
before applying eol_scons.  In theory, the insertion of the eol_scons default
tool should not affect scons builds which worked using the default tool
without eol_scons.  The eol_scons default tool also optimizes the loading of
all the default tools, helping to speed up builds which create many
`Environment`s.

It is also possible to apply eol_scons to an `Environment` like a regular
tool, without overriding the default tool, but this is an experimental
technique.  In this case, an `Environment` which needs the eol_scons
extensions must explicitly load a tool module called `eol_scons_tool.py`.  If
eol_scons has been imported, then the `eol_scons_tool.py` module will be on the
tool path already, but the default tool override will also be on the path.  So
the default tool can be removed from the tool path using the
`RemoveDefaultHook()` function:

```python
import eol_scons
eol_scons.RemoveDefaultHook()
env = Environment(tools=['default', 'eol_scons_tool', 'prefixoptions', 'netcdf'])
```

If someone wants to load the tool without an explicit import in the
`SConstruct` file, then `eol_scons_tool.py` can be copied or linked into one
of the scons site_tools directories. Then when loaded into an Environment, it
takes care of first importing eol_scons, removing the default hook, and then
customizing the Environment.  The code below is an example.  It applies the
eol_scons extensions to the created Environment but does not override the
default tool and does not require an explicit import.  It just requires that
the `eol_scons_tool.py` tool module be installed (or linked) somewhere in the
scons tool path.

```python
env = Environment(tools=['default', 'eol_scons_tool', 'prefixoptions', 'netcdf'])
variables = env.GlobalVariables()
```

Unfortunately, `scons` does not have a command-line option to modify the
tool path.  Maybe the eol_scons/tools directory should be renamed to
site_tools, then eol_scons_tool.py could be added to the tool path by
specifying eol_scons as the site directory.  For this to work the eol_scons
package must still be on the python path.

```python
scons --site-dir=/usr/share/scons/site_scons/eol_scons
```

### External Tools

Below is an example of a very simple tool from eol_scons for building against
the fftw library.  The [fftw](eol_scons/tools/fftw.py) tool is a tool file in
the `eol_scons/tools` directory under the top directory of the project source
tree.  It's a shared tool file because it is always an external dependency.

```python
def generate(env):
  # Hardcode the selection of the threaded fftw3, and assume it's installed
  # somewhere already on the include path, ie, in a system path.
  env.Append(LIBS=['fftw3_threads','fftw3'])

def exists(env):
    return True
```

A source module which depends on `fftw` could include this tool in
a SConscript Environment file like so:

```python
env = Environment(tools = ['default', 'fftw'])
```

### Internal Tools

Tools can also be defined locally, to add tools beyond those defined in
`site_scons/site_tools`.  This is as simple as `def`-ing and `Export`-ing a
SCons function, the name of which is the name of the tool. This can happen in
a SConscript file, in which case the tool will be defined as soon as the
SConscript file is loaded.  However, a file does not have to be loaded
explicitly if the tool is contained in a file named `tool_{toolname}.py`.  The
`eol_scons` package will try to find and load such a tool file from within the
local hierarchy when a tool name is requested. The `tool_*.py` files are
loaded like regular SConscript files using the `SConscript()` function, unlike
tool modules which are imported as python modules.  See
[tool_logx.py](examples/logx/tool_logx.py) for an example.

Tools are not limited to changing the library and include paths in the
`Envrionment` construction variables. Tools can also modify the methods
available on an `Environment` to provide new functionality.  For example, the
`doxygen` tool adds the `Apidocs()` build wrapper ("pseudo-builder") to an
`Environment`.

A `SConscript` file might create an `Environment` that requires `logx` like
so:

```python
env = Environment(tools = ['default', 'logx'])
```

Modules which use the `logx` tool do not need to know the dependencies of the
`logx` library.  If the library ever adds another external library as a
dependency, that dependency only needs to be added to the `logx` tool function
and nowhere else.

The `logx` tool in turn requires the `log4cpp` tool, but that tool is defined
in a tool module file included in `eol_scons`:
[log4cpp.py](eol_scons/tools/log4cpp.py).  A tool module defines a function
called `generate()` to modify an `Environment`.  The `generate()` module
function serves the same purpose as the python tool function defined in a
`SConscript` or `tool_*.py` file.  See the
[log4cpp.py](eol_scons/tools/log4cpp.py) file for an example.

## The eol_scons Package

The eol_scons package extends the standard SCons framework for EOL
software developments.

### site_scons Directory

The eol_scons modules and tools reside in a directory meant to be shared among
software projects.  The idea is that this directory should hold the files for
a project build framework which are not specific to a particular project.  The
directoy can be linked into a source tree, checked out separately, or included
as a _git_ submodule or _svn_ external.  SCons automatically checks for a
directory called `site_scons` in the top directory, where the `SConstruct`
file is located.  So one common way to include eol_scons in a project is to
clone it under the `site_scons` directory, usually as a git submodule.  See
the install information in [README.md](README.md).

### SCons Extensions

This package extends SCons in three ways.  First of all, it overrides or adds
methods in the SCons `Environment` class.  See the `AddMethods()` function in
[eol_scons/methods.py](eol_scons/methods.py) and the `generate()` function in
[eol_scons/tool.py](eol_scons/tool.py) to see the full list.

Second, this package adds a set of EOL tools to the SCons tool path.  Most of
the tools there are for configuring and building against third-party software
packages.

Lastly, this module itself provides an interface for configuring and
controlling the eol_scons framework outside of the Environment methods.  The
following sections cover the public functions.

## Examples

Below are some examples of projects which use eol_scons:

- Library: [logx](https://github.com/NCAR/logx/)
- Library: [domx](https://github.com/NCAR/domx)
- Full project: [NIDAS](https://github.com/NCAR/nidas)
- Single application: [acTrack2kml](https://github.com/NCAR/kml_tools/tree/master/acTrack2kml)

For EOL developers, these projects are also good examples, but they are not
public:

- [AEROS](https://github.com/NCAR/aeros)
- [ASPEN](https://github.com/NCAR/aspen)

The libraries contain examples of SConscript files and tools for embedding a
module into another project.  The [NIDAS
SConstruct](https://github.com/ncareol/nidas/blob/master/src/SConstruct) is a
good example of a few techniques:

- Providing both brief and verbose help for build settings and aliases.
- Variant builds derived from target OS and architecture.
- Separating config from build to enable `-Werror` on compile.

## Global Variables

The `GlobalVariables()` function returns the global set of variables (formerly
known as options) available in this source tree.  Recent versions of SCons
provide a global `Variables` singleton by default, but this method supplies a
default config file path.  The first `Variables` instance to be constructed
with `is_global=1` (the default) becomes the singleton instance, and only that
constructor's settings (for config files and arguments) take effect.  All
other `Variables()` constructors will return the singleton instance, and any
constructor parameters will be ignored.  If a particular source tree wants to
set its own config file name, it can specify that path in a `Variables()`
constructor in the top-level SConstruct, so that instance is created before
the default created by eol_scons:

SConstruct:

```python
variables = Variables("my_settings.py")
```

If no singleton instance is created explicitly by the project SConsctruct
file, then the default created by eol_scons will take effect.  The default
`eol_scons` `Variables()` instance specifies a config file called `config.py`
in the top directory.

Use the `GlobalVariables()` function to add configurable options from any tool
or SConscript file used in a project.

For example, the spol package script adds an option `SPOL_PREFIX`:

```python
print "Adding SPOL_PREFIX to options."
eol_scons.GlobalVariables().AddVariables (
    PathVariable('SPOL_PREFIX', 'Installation prefix for SPOL software.',
           '/opt/spol'))
```

The option is only added once, the first time the `spol.py` tool is loaded.
After that, every time the spol tool is applied it calls Update() on the
target environment to make sure the spol configuration options are setup in
that environment.

```python
    eol_scons.GlobalVariables().Update(env)
```

## Global Tools

The eol_scons environment adds the notion of global tools, or tools which can
be specified in root environments which will be applied to all subdirectory
Environments.  The global tools are mapped by the particular directory of the
`SConscript` or `SConstruct` file which created the Environment.  Each
`Environment` can specify its own set of global tools. Those tools, plus the
global tools of any environments created in parent directories, will be
applied to all `Environment` instances created in any subdirectories.  In
other words, nested project trees can extend the global tools set with the
tools needed by its subdirectories, but those tools will not be applied in
other directories of the project.  One project can contain other source trees
each with their own `SConstruct` file.  Those `SConstruct` files can be loaded
with normal SConscript calls, but their global tools list will only affect the
directories within the subproject.

A typical `SConstruct` file appends a global tool function and other tools to
its global tools.  Global tools are the hook by which the `SConstruct` file
can provide the basic configuration for an entire source tree if needed,
without specifying the same set of tools every time an `Environment` is
created within a project.  Global tools are specific to the directory in which
an `Environment` is created, and its subdirectories.

The global tools can be extended by passing the list of tools in the
`GLOBAL_TOOLS` construction variable when creating an Environment:

```python
import eol_scons
env = Environment(tools = ['default'],
                  GLOBAL_TOOLS = ['svninfo', 'qtdir', 'doxygen', Aeros])
```

Or, for an existing `Environment` instance, the global tool list can be
modified like below, using the `GlobalTools()` method.

```python
  env.GlobalTools().extend([Aeros, "doxygen"])
```

The `GlobalTools` method is one of the customizations added by `eol_scons`
when an `Environment` is created.

In the above method, the new tools will *not* be applied to `env`.
The tools *are* applied when passed in the `GLOBAL_TOOLS` keyword in an
`Environment` constructor.

Global tools are never applied retroactively to existing environments, only
when environments are created.  Once an Environment has been created, tools
must be applied using the `Tool()` or `Require()` methods.

A simple example is using a global tool to add compiler flags which should
used throughout a source tree:

```python
import eol_scons

env = Environment(tools=['default'])

def global_setup(env: Environment):
    env.AppendUnique(CFLAGS=['-Wall'])
    env.AppendUnique(CCFLAGS=['-g', '-O2'])
    # env.Append(CCFLAGS=['-O0'])
    env.AppendUnique(CXXFLAGS=['-Wall', '-Wextra'])
    env.AppendUnique(CCFLAGS=['-Wformat', '-Werror=format-security'])

env.RequireGlobal(global_setup)

SConscript("libutils")
SConscript("libcore")
SConscript("apps")
```

In this case, `RequireGlobal` is sufficient if no source files are compiled
with `env`.

By breaking up `Environment` setup into tools, rather than sharing a single
`Environment` through the whole source tree, each `Environment` can be
composed with only the tools needed to build each component in the source
tree.  When necessary, global tools apply customizations intended for every
subdirectory, without having to add those tools to every subdirectory.  For
code which is shared across projects, the submodule only specifies the tools
required by that submodule, but it also automatically applies the particular
global tools for each project in which it is built.

## Debugging

`Debug(msg)` prints a debug message if the global debugging flag is true.

`SetDebug(enable)` sets the global debugging flag to `enable`.

The debugging flag in `eol_scons` can also be set using the SCons Variable
`eolsconsdebug`, either passing `eolsconsdebug=1` on the scons command line or
setting it in the `config.py` file like any other variable.

## Technical Details on Tools and eol_scons

The eol_scons package overrides the standard `Tool()` method of the SCons
`Environment` class to customize the way tools are loaded.  First of all, the
eol_scons `Tool()` method loads a tool only once.  In contrast, the standard
SCons method reloads a tool through the python `imp` module every time a tool
name is referenced, and at this point some of the eol_scons tools may rely on
being loaded only once.

Loading a tool is different than applying it to an `Environment`.  Loading a
tool module only once means the code in the module runs only once.  So for
example, variables with module scope should only be initialized once. However,
some tools still contain code to check whether module-scope variables have
been initialized already or not, in case the tool is ever used where it can be
loaded multiple times.  There are also guards against initializing more than
once within the tool function, since the tool can be applied multiple times to
the same or different `Environment`s.

At one point eol_scons tried to apply tools only once.  Standard SCons keeps
track of which tools have been loaded in an environment in the `TOOLS`
construction variable, but it always applies a tool even if it's been applied
already.  The `TOOLS` variable is a dictionary of `Tool` instances keyed by
the module name with which the tool was loaded (imported). However, sometimes
this module name was inconsistent depending upon how and where a tool is
referenced.  So `eol_scons.Tool()` uses its own dictionary keyed just by the
tool name.  Applying a tool only once seems to work, however it might violate
some other assumptions about setting up a construction environment.  For
example, dependencies may need to have their libraries listed last, after the
last component which requires them, but this won't happen if the required tool
is required twice but only applied the first time.  More experience might
determine if it makes more sense to only apply tools once, but for now
eol_scons follows the prior practice of applying tools multiple times, which
is consistent with the standard SCons behavior.

The eol_scons package also adds a `Require()` method to the SCons
Environment.  The `Require()` mehod simply loops over a tool list calling
`Tool()`.  The customized eol_scons `Tool()` method returns the tool that was
applied, as opposed to the `SCons.Environment.Environment` method which does
not.  This makes it possible to use `Require()` similarly to past usage,
where it returns the list of tools which should be applied to environments
built against the component:

```python
env = Environment(tools = ['default'])
tools = env.Require(Split("doxygen qt"))

def this_component_tool(env):
    env.Require(tools)

Export('this_component_tool')
```

It should be possible to make tools robust enough to only execute certain code
once even when loaded multiple times, but that hasn't been explored much to
find a solution that's not more work than it's worth.

Tools are python modules and not SConscript files, so certain functions and
symbols are not available in the global namespace as they are in SConscript
files.  The symbols available globally in a SConscript file can be imported
by a tool from the `SCons.Script` package.  Here's an example:

```python
import SCons.Script
SCons.Script.Export('gtest')
from SCons.Script import BUILD_TARGETS
```

To refer to tools defined in SConscript files in other directories within a
source tree, `Export()` the tool function in the SConscript file, then just
reference the exported name as a tool in the SConscript files which need it,
such as in the `tools` argument to `Environment()` or in the `Require()` or
`Tool()` methods.  See the examples section for projects which demonstrate
this.

## Configuration

The eol_scons framework contains a tool called `prefixoptions`.  The tool adds
build variables called `OPT_PREFIX` and `INSTALL_PREFIX`.  `OPT_PREFIX`
defaults to `$DEFAULT_OPT_PREFIX`, which in turn defaults to `/opt/local`.  A
source tree can modify the default by setting `DEFAULT_OPT_PREFIX` in the
environment in a global tool.  Run `scons -h` to see the help information for
all of the local options.  An option can be set on the command line like this:

```python
scons -u OPT_PREFIX=/opt
```

It also can be set in a file called `config.py` in the top directory:

```python
# toplevel config.py
OPT_PREFIX="/opt"
```

The `OPT_PREFIX` path is automatically included in the appropriate compiler
options.  Several smaller packages expect to be found there by default, in
which case they might not add any paths to the environment themselves, relying
instead on the global settings.

The `INSTALL_PREFIX` option is the path prefix used by the custom install
methods:

```python
InstallLibrary(source)
InstallProgram(source)
InstallHeaders(subdir, source)
```

Therefore the above methods do not exist in the environment instance until
the prefixoptions tool has been loaded.

The `INSTALL_PREFIX` defaults to the value of `OPT_PREFIX`.

Finally, the end of the top-level SConstruct file should contain a call to the
SCons `Help()` function using the help text from the `GlobalVariables()`
instance.  This ensures that any options added by any of the modules in the
build tree will appear in the output of `scons -h`.

```python
options = env.GlobalVariables()
options.Update(env)
Help(options.GenerateHelpText(env))
```

## SCons Doxygen

See the documentation in the [doxygen.py](eol_scons/tools/doxygen.py) tool.

## Speeding Up Builds

There are a few ways to speed up iterative scons builds using eol_scons.  See
these tools for ideas: ninja_es ([ninja_es.py](eol_scons/tools/ninja_es.py)),
rerun ([rerun.py](eol_scons/tools/rerun.py)), and dump_trace
([dump_trace.py](eol_scons/tools/dump_trace.py)).

## Building Subsets of the Source Tree

SConscript files in eol_scons projects usually do not import a root
environment from which to create their own environment.  Instead they use the
normal SConscript convention of creating their own `Environment` with the
`default` tool, which may or may not need to be modified by a global tool.
For example, it is possible to build the `logx` library separately from the
rest of the source tree with something like below.  If `eol_scons` is not in
one of the default `site_scons` search locations, then the location can be
added with `--site-dir`.

```python
cd logx
scons -f SConscript --site-dir ../site_scons
```

With a few tweaks to the `SConscript` file, many library source directories
use the same `SConscript` file to build both within a source tree and
standalone.
