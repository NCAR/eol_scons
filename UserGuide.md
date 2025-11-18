# User Guide for eol_scons

## Overview

This `eol_scons` software configuration package is an extension to
[SCons](https://scons.org) for modularizing the commands and configuration
required to build software. Libraries and executables can be compiled and
shared across the whole tree, without knowing whether dependencies are
internal or external to the tree. Likewise options for configuring the build
can be defined in one place but shared across all modules which use need those
options.

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
any other tool.  In particular, they can be applied with the `Tool()` method or
passed in the tools list when the Environment is constructed.

### Installation

See [README.md](README.md) for installation.

### Activating eol_scons

There are two parts to extending SCons with eol_scons.  The first part is
inserting eol_scons into the scons tool path so that eol_scons can override
some of the standard SCons tools.  This modifies the global scons state
rather than just one Environment instance.  The second part to extending
SCons is the customization of an Environment instance.  This is the part
that behaves like a normal scons tool.

Installing eol_scons on the python search path does not automatically
activate it within a SCons build.  The eol_scons tools are not on the
default tool path, and eol_scons does not install a site_init.py file.

The first part happens when eol_scons is imported, when it automatically
inserts the eol_scons tools directory into the scons tool path.  It also
inserts a second tools directory containing a default.py tool module to
override the scons default tool.  By overriding the default tool, eol_scons
can apply itself to every Environment created by scons to which the 'default'
tool is applied, which usually is every Environment in a source tree.  This is
the usual way to activate eol_scons in a scons build, since it avoids
explicitly applying eol_scons to every Environment constructor call.  To
activate eol_scons this way, import eol_scons at the top of the SConstruct
file, before any tools are loaded:

```python
import eol_scons
...
env = Environment(tools=['default'])
```

The overridden default tool first applies the standard scons default tools
before applying eol_scons.  In theory the insertion of the eol_scons
default tool should not affect scons builds which worked using the default
tool without eol_scons.  Plus the eol_scons default tool optimizes the
loading of all the default tools, helping to speed up builds which create
many Environments.

It is also possible to apply eol_scons to an Environment like a regular
tool, without overriding the default tool, but this is an experimental
technique.  In this case, Environments which need the eol_scons extensions
must explicitly load a tool module called eol_scons_tool.py.  If eol_scons
has been imported, then the eol_scons_tool.py module will be on the tool
path already, but the default tool override will also be on the path.  So
the default tool can be removed from the tool path using the
RemoveDefaultHook() function:

```python
import eol_scons
eol_scons.RemoveDefaultHook()
env = Environment(tools=['default', 'eol_scons_tool', 'prefixoptions', 'netcdf'])
```

If someone wants to load the tool without an explicit import in the
SConstruct file, then eol_scons_tool.py can be copied or linked into one of
the scons site_tools directories. Then when loaded into an Environment, it
takes care of first importing eol_scons, removing the default hook, and
then customizing the Environment.  The code below is an example.  It
applies the eol_scons extensions to the created Environment but does not
override the default tool and does not require an explicit import.  It just
requires that the eol_scons_tool.py tool module be installed (or linked)
somewhere in the scons tool path.

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
the fftw library.  The `fftw` tool is a tool file in the `eol_scons/tools`
directory under the top directory of the project source tree.  It's a shared
tool file because it's always an external dependency.

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

Tools can also be defined locally, to extend beyond the tools which are
defined in `site_scons/site_tools`.  This is as simple as `def`-ing and
`Export`-ing a SCons function, the name of which is the name of the tool.
This can happen in a SConscript file, in which case the tool will be defined
as soon as the SConscript file is loaded.  However, the preferred method is to
create a file named `tool_{toolname}.py` in the directory containing the
tool's components.  The `eol_scons` package will try to find and load such a
tool definition from within the local heirarchy when a tool is requested, so
there's no need to explicitly load a specific `SConscript` file before
requesting the tool.  Here's an example tool definition from the ELDORA tree,
where a tool named `ddslib` is defined in file `ddslib/tool_ddslib.py`:

```python
#
# Rules to build ddslib and export it as a SCons tool
#
tools = ['opendds', 'doxygen']
env = Environment(tools = ['default'] + tools)

def ddslib(env):
    env.AppendLibrary('EldoraDds')
    env.AppendDoxref('EldoraDds')
    env.AppendUnique(CPPPATH = ['#/ddslib',])
    env.Require(tools)

Export('ddslib')

libEldoraDds, sources, headers = env.DdsLibrary('EldoraDds.idl', env)

html = env.Apidocs(sources + headers, DOXYFILE_FILE = "#/Doxyfile")

Default(libEldoraDds)
```

Creation of a tool requires only that a function be `def`-ed and
`Export`-ed.  Everything else shown above is the details for actually
building the library provided by the `ddslib` tool.  Simpler tools would
just use the normal SCons builder methods like `env.Program()` and
`env.Library()`.

The `ddslib` example shows how tools are not limited to affecting the
library and include paths through the Envrionment's construction variables.
Tools can also modify the methods available on an Environment to provide
new conveniences or functionality.  For example, the 'doxygen' tool adds
the 'Apidocs()' build wrapper ("pseudo-builder") to the Environment.

Also note how the tool requirements are recursive.  When another
environment requires tool 'ddslib', the `EldoraDDS` library is added to the
library path.  In addition, all the requirements of the EldoraDDS library
are added by the call to `env.Require(tools)`.  In particular, requiring
the 'opendds' tool (which was required to build the EldoraDDS library) will
add the OpenDDS libraries to the library path which EldoraDDS will need to
link successfully.

Here's how a `SConscript` might show that it requires 'ddslib':

```python
tools = ['ddslib', 'qt4']
env = Environment(tools = ['default'] + tools)
```

The above excerpt creates an Environment which loads a tool called 'ddslib'
(along with 'qt4').  If the tool 'ddslib' had not been found in the global
exports as 'ddslib' or 'PKG_DDSLIB', then eol_scons would have looked for a
file named `tool_ddslib.py` in the local hierarchy and loaded it to
generate the tool, otherwise it would have continued to look via the normal
SCons tool mechanism.

Note that modules which use the 'ddslib' component do not need
to know the dependencies of the ELDORA DDS library.  If the library
adds another external library as a dependency, then that dependency will
be added in the `ddslib` tool definition.

Here's an example from the 'logx' tool.  This is an external tool file,
meaning it is contained in the site_scons/site_tools on the normal scons
tool path, rather than being located within a source directory in a
`tool_*.py file`.  The tool_.py files are loaded like regular SConscript
files with the SConscript() function, whereas tool modules are imported as
python modules.  A tool module must define a function called 'generate' to
modify an environment.  The generate() module function serves the same
purpose as the python tool function defined in a `SConscript` or
`tool_*.py` file.

```python
def generate(env):
    env.AppendLibrary ("logx")
    if env.GetGlobalTarget("liblogx"):
          env.AppendDoxref("logx")
    else:
          env.AppendDoxref("logx:/net/www/software/raddx/apidocs/logx/html")
    env.Tool ('log4cpp')
```

Since the logx library requires log4cpp, the logx tool automatically sets
up the log4cpp dependencies with the 'env.Tool()' call.

The logx tool appends the liblogx target to the list of libraries and then
requires the log4cpp tool, which in turn appends the log4cpp dependencies
to the environment.  Any other module in the source tree which applies only
the logx tool to its environment will in turn have log4cpp applied
automatically.  If the logx library someday requires another library or
other include paths, none of the other modules in the source tree which use
logx will need to change their SConscript configuration.

Unlike in the log4cpp.py tool file, liblogx is a library normally built
_within_ the source tree, and so the actual liblogx target node is added to
the LIBS construction variable.  The liblogx target node must be retrieved
from a global registry of such nodes maintained by the eol_scons
package.  The logx tool could just as well determine whether the logx
library should be linked from within the source tree or from some external
installation, and then modify the environment accordingly.  The source
module which depends upon the logx library need not change either way.

## The eol_scons Package

The eol_scons package extends the standard SCons framework for EOL
software developments.

### site_scons Directory

The eol_scons modules and tools reside in a directory meant to be shared among
software projects.  The idea is that this directory should hold the files for
a project build framework which are not specific to a particular project.  The
directoy can be linked into a source tree, checked out separately, or
referenced using 'svn:extnerals'.  SCons automatically checks for a directory
called 'site_scons' in the top directory, where the SConstruct file is
located.  So by checking out the eol_scons directory tree into a directory
called 'site_scons', the integration and extension of SCons happens
automatically.  See also the installation information in
[README.md](README.md).

### extensions SCons Extensions

This package extends SCons in three ways.  First of all, it overrides or
adds methods in the SCons Environment class.  See the
eol_scons._addMethods() function to see the full list.

Second, this package adds a set of EOL tools to the SCons tool path.  Most
of the tools there are for configuring and building against third-party software
packages.

Lastly, this module itself provides an interface for configuring and
controlling the eol_scons framework outside of the Environment methods.  The
following sections cover the public functions.

### Examples

Below are some examples of projects which use eol_scons:

- Library: [logx](https://github.com/NCAR/logx/)
- Library: [domx](https://github.com/NCAR/domx)
- Full project: [NIDAS](https://github.com/ncareol/nidas)
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

## GlobalVariables()

The `GlobalVariables()` function returns the global set of variables
(formerly known as options) available in this source tree.  Recent versions
of SCons provide a global `Variables` singleton by default, but this method
supplies a default config file path.  The first `Variables` instance to be
constructed with `is_global=1` (the default) becomes the singleton
instance, and only that constructor's settings (for config files and
arguments) take effect.  All other `Variables()` constructors will return the
singleton instance, and any constructor parameters will be ignored.  So if
a particular source tree wants to set its own config file name, it can
specify that path in a `Variables()` constructor in the top-level SConstruct,
so that instance is created before the default created by eol_scons:

SConstruct:

```python
variables = Variables("my_settings.py")
```

If no singleton instance is created explicitly by the project SConsctruct
file, then the default created by eol_scons will take effect.  The default
`eol_scons` `Variables()` instance specifies a config file called `config.py`
in the top directory.

## Global Tools

The eol_scons environment adds the notion of global tools, or tools which
can be specified in root environments which will be applied to all
subdirectory Environments.  Originally their use was limited to the
top-level SConstruct file.  It could create an environment which specified
a set of tools that the project would apply to each Environment created.
With the advent of nested projects, the global tools are now mapped by the
particular directory of the SConscript or SConstruct file which created the
Environment.  Each Environment can specify its own set of global tools.
Those tools, plus the global tools of any Environments created in parent
directories, will be applied to all Environments created in any
subdirectories.  In other words, nested project trees can extend the global
tools set with the tools needed by its subdirectories, but those tools will
not be applied in other directories of the project.  One project can
contain other source trees each with their own SConstruct file.  Those
SConstruct files can be loaded with normal SConscript calls, but their
global tools list will only affect the directories within the subproject.

A typical SConstruct file appends a global tool function and other tools to
its global tools.  Global tools are the hook by which the SConsctruct file
can provide the basic configuration for an entire source tree if needed,
without requiring a redundant set of tools to specified every time an
Environment is created within a project.  Global tools are specific to the
directory in which an Environment is created.  They can be modified in 
one of two ways.

The global tools can be extended by passing the list of tools in the
GLOBAL_TOOLS construction variable when creating an Environment:

```python
  env = Environment(tools = ['default'],
                    GLOBAL_TOOLS = ['svninfo', 'qtdir', 'doxygen', Aeros])
```

Or, for an environment has already been created, the global tool list can
be modified like below:

```python
  env.GlobalTools().extend([Aeros, "doxygen"])
```

However, in the above method, the new tools will *not* be applied to the
Environment.  The tools *are* applied when passed in the GLOBAL_TOOLS
keyword in an Environment constructor.

Global tools are never applied retroactively to existing environments, only
when environments are created.  Once an Environment has been created, tools
must be applied using the Tool() or Require() methods.

## Debugging

`Debug(msg)` prints a debug message if the global debugging flag is true.

`SetDebug(enable)` sets the global debugging flag to `enable`.

The debugging flag in `eol_scons` can also be set using the SCons Variable
`eolsconsdebug`, either passing `eolsconsdebug=1` on the scons command line or
setting it in the `config.py` file like any other variable.

## Technical Details on Tools and eol_scons

The eol_scons package overrides the standard Tool() method of the SCons
Environment class to customize the way tools are loaded.  First of all, the
eol_scons Tool() method loads a tool only once.  In contrast, the standard
SCons method reloads a tool through the python 'imp' module every time a
tool name is referenced, and this seems excessive and unnecessary, and at
this point some of the eol_scons tools may rely on being loaded only
once.

Loading a tool is different than applying it to an 'Environment'.  Loading
a tool module only once means the code in the module runs only once.  So
for example, variables with module scope should only be initialized once.
However, some tools still contain code to check whether module-scope
variables have been initialized already or not, in case the tool is ever
used where it can be loaded multiple times.  There are also guards against
initializing more than once within the tool function, since the tool can be
applied multiple times to the same or different 'Environments'.

At one point eol_scons tried to apply tools only once.  Standard SCons
keeps track of which tools have been loaded in an environment in the TOOLS
construction variable, but it always applies a tool even if it's been
applied already.  The TOOLS variable is a dictionary of Tool instances
keyed by the module name with which the tool was loaded (imported).
However, I think I found this name to be inconsistent depending upon how
and where a tool is referenced.  So eol_scons.Tool() uses its own
dictionary keyed just by the tool name.  Applying a tool only once seems to
work, however it might violate some other assumptions about setting up a
construction environment.  For example, dependencies may need to have their
libraries listed last, after the last component which requires them, but
this won't happen if the required tool is required twice but only applied
the first time.  More experience might determine if it makes more sense to
only apply tools once, but for now eol_scons follows the prior
practice of applying tools multiple times, which is consistent with the
standard SCons behavior.

The eol_scons package also adds a Require() method to the SCons
Environment.  The Require() mehod simply loops over a tool list calling
Tool().  The customized eol_scons Tool() method returns the tool that was
applied, as opposed to the SCons.Environment.Environment method which does
not.  This makes it possible to use Require() similarly to past usage,
where it returns the list of tools which should be applied to environments
built against the component:

```python
env = Environment(tools = ['default'])
tools = env.Require(Split("doxygen qt"))

def this_component_tool(env):
    env.Require(tools)

Export('this_component_tool')
```

It should be possible to make tools robust enough to only execute certain
code once even when loaded multiple times, but that hasn't been explored
much to find a solution that's not more work than it's worth.  [As far as
I'm concerned, it seems legitimate to assume that a module or tool is only
ever loaded once.  That's why the eol_scons Tool() method overrides the
scons standard method to only load a tool once.]

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
source tree, Export() the tool function in the SConscript file, then just
reference the exported name as a tool in the SConscript files which need it,
such as in the `tools` argument to `Environment()` or in the `Require()` or
`Tool()` methods.  See the examples section for projects which demonstrate
this.

## Configuration

The eol_scons framework contains a tool called 'prefixoptions'.  It
used to be part of the environment by default, but now it is a separate
tool.  However, the tool is still loaded by default unless the
GlobalTools() list is modified first.  The tool adds build options called
`OPT_PREFIX` and `INSTALL_PREFIX`.  `OPT_PREFIX` defaults to
`$DEFAULT_OPT_PREFIX`, which in turn defaults to `/opt/local`.  A source
tree can modify the default by setting `DEFAULT_OPT_PREFIX` in the
environment in the global tool.  Run `scons -h` to see the help information
for all of the local options.  You can set an option on the command line
like this:

```python
scons -u OPT_PREFIX=/opt
```

Or you can set it for good in a file called `config.py` in the top
directory:

```python
# toplevel config.py
OPT_PREFIX="/opt"
```

The `OPT_PREFIX` path is automatically included in the appropriate
compiler options.  Several of the smaller packages expect to be found there
by default (eg, netcdf), and so they don't add any paths to the environment
themselves.

The `INSTALL_PREFIX` option is the path prefix used by the installation
methods of the Pkg_Environment class:

```python
InstallLibrary(source)
InstallProgram(source)
InstallHeaders(subdir, source)
```

Therefore the above methods do not exist in the environment instance until
the prefixoptions tool has been loaded.

The `INSTALL_PREFIX` defaults to the value of `OPT_PREFIX`.

It is also possible for any package script or SConscript to add more
configuration options to the build framework.  The eol_scons package creates a
single instance of the SCons Variables class, and that is the instance to
which the `OPT_PREFIX` and `INSTALL_PREFIX` options are added.  The eol_scons
function `GlobalVariables()` returns a reference to the global Variables
instance, so further options can be added at any time by adding them to that
instance.

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

Individual SConscript files do not always need to import a root environment
from which to create their own environment.  Instead they use the normal
SConscript convention of creating their own `Environment` with the `default`
tool, which may or may not need to be modified by a global tool.  For example,
it is possible to build the `logx` library separately from the rest of the
source tree with something like below.  If `eol_scons` is not in one of the
default `site_scons` search locations, then the location can be added with
`--site-dir`.

```python
cd logx
scons -f SConscript --site-dir ../site_scons
```

With a few tweaks to the `SConscript` file, many library source directories
use the same `SConscript` file to build both within a source tree and
standalone.
