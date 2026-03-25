# README eol_scons

Following is the quick introduction to using and installing `eol_scons`. Also
see the [CHANGELOG.md](CHANGELOG.md) and [UserGuide.md](UserGuide.md).

An example project is included in the `templates` subdirectory to demonstrate
basic eol_scons features and serve as a template for new projects. See
[templates/Templates.md](templates/Templates.md) for an overview.

## Quick Start

In the `SConstruct` file, `import eol_scons`. The import adds
`eol_scons/tools` to the `SCons` tool search path.

```python
import eol_scons
env = Environment(tools=['default'])
```

In particular, every `Environment` created with the `default` tool, including
in any subsequent `SConscript` calls, will automatically get the standard
`eol_scons` extensions.

The `eol_scons` tools are applied to an `Environment` instance like any other
`SCons` tool.  Many of the `eol_scons` tools add methods to the instance
related to their purpose.  For example, the `testing` tool
([testing.py](eol_scons/tools/testing.py)) adds pseudo-builder methods
`DefaultTest` and `TestLog` and the `Diff` builder.

Generally, each subdirectory has its own `SConscript` file, and that file
creates one or more `Environment` instances configured to build just the code
in that directory.  This allows build dependencies to be isolated from the
rest of the project.  Compile and link flags needed to build in one directory
do not need to be added to the build environment for another directory.
Environments do not need to be passed down to other `SConscript` files with
`Export`.  This allows projects to be composed of smaller components, but
because the components are added as dependencies using tools, the rest of the
project does not need to know how that component is built or even where it is
located, either in the tree or outside of it.

Global tools can be applied to every `Environment` created, without requiring
the tools be loaded explicitly everywhere.  There is also support for a global
`Variables` instance, so a tool can add it's own variables once and use the
same settings across all the `Environment` instances which apply that tool

See the [UserGuide.md](UserGuide.md) for more information.

## Installing eol_scons

By default, SCons looks for extensions and additional tools in _site
directories_ named `site_scons`.  The standard locations for different
platforms are listed in the documentation for the `--site-dir` command line
option on the [SCons man
page](https://scons.org/doc/production/HTML/scons-man.html). On all platforms,
the site directory with the highest precedence is `./site_scons`, in the same
directory as `SConstruct`.  Therefore, several different ways to add
`eol_scons` to a `SCons` build are listed in the following sections.

Note that `eol_scons` does not use a `site_init.py` file or a `site_tools`
directory to inject itself into the `SCons` build.  If it did, it would have
to be cloned with the name `site_scons`, and the `site_init.py` file and the
`site_tools` directory would be part of the `eol_scons` source.  This
precludes adding other `SCons` extensions alongside `eol_scons` in the same
`site_scons` directory, whether it's the local project `./site_scons` or a
system location like `/usr/share/scons/site_scons`.

Instead, `eol_scons` injects itself into `SCons` when it is imported.  This
means `eol_scons` only needs to be available on the Python system path.  Since
`SCons` adds all the `site_scons` directories to the system path, that allows
the `eol_scons` directory to be imported when it is installed or cloned into a
`site_scons` directory.  If a site or project wants to add other tools using a
`site_init.py` or `site_tools`, then `eol_scons` does not prevent that.
Further, there is a great deal of flexibility in installing `eol_scons` as a
python package instead of under a `site_scons` directory, since it can be
managed with all the common Python virtual environment tools, including `pip`
and `pipenv`.

Note that `eol_scons` is _not_ a `SCons` _tool package_.  It does not provide
the `generate()` or `exists()` methods required in scons tools. So there is no
point to installing the `eol_scons` package under one of the `site_tools`
directories searched by `SCons`.  Instead, `eol_scons` is meant to be
installed as a python package or in one of the `site_scons` search paths, as
described below.

### Installing as a python package

The `eol_scons` source includes a `pyproject.toml` file for building a python
package.  Probably the most convenient way to add it to a `SCons` build
environment for a specific project is with `pipenv`.  Below is an example,
using an existing clone of `eol_scons` under the home directory.

```sh
pipenv install -e ~/.scons/site_scons/eol_scons/
```

That installs the `eol_scons` python package in _editable_ mode into the
virtual environment associated with the project's top directory, and since
`scons` is a dependency of `eol_scons`, the `scons` package is installed also.
The project's virtual environment can be used to run a `scons` build, and the
`eol_scons` extensions will be available for import since they are installed
into that virtual environment:

```sh
pipenv run scons
```

`pipenv` is especially convenient when project-specific `SCons` builds have
other python dependencies.  A project with other python requirements, such as
the `requests` package, can create a `requirements.txt` file like below.

```
eol_scons @ https://github.com/NCAR/eol_scons/archive/refs/heads/master.zip
requests
```

Then the `scons` build environment can be created without needing to first
clone or install `eol_scons` somewhere else:

```sh
pipenv install
```

Of course similar approaches can be used with `pip` to install `eol_scons`
into other python virtual environments.

The source and wheel packages can be built like below, assuming the python
`build` package is installed in the current python environment.

```sh
python -m build
```

The resulting wheel in `./dist` can then be installed into a python virtual
environment, same as above.

### Install to $HOME/.scons/site_scons

`eol_scons` can be cloned into the `site_scons` directory, so that other SCons
extensions can be installed under `site_scons` also.

```shell
mkdir -p $HOME/.scons/site_scons
cd $HOME/.scons/site_scons
git clone https://github.com/ncar/eol_scons
```

### RPM for RedHat Linux systems

The RPM package installs eol_scons to `/usr/share/scons/site_scons`.  The RPM
is available for a few systems from the EOL yum repository.

Enable the EOL yum repository on RHEL systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-epel.noarch.rpm
```

On Fedora systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-fedora.noarch.rpm
```

Install the RPM:

```shell
sudo yum install eol_scons
```

As mentioned earlier, RPM installs are not as flexible or even as convenient
as installing the `eol_scons` package into a python virtual environment, so
the RPMs may be deprecated someday.

### Install from source to rpm path

To install `eol_scons` from source to the same location as the RPM package, use
this command:

```shell
scons PREFIX=/usr/share/scons/site_scons install
```

### Install to project site_scons

Create the `./site_scons` subdirectory in the directory containing `SConstruct`,
then clone `eol_scons` into it same as above.

### Access as a git submodule

In a git repository, in the same directory as `SConstruct`, where vX.Y is
the tagged branch of eol_scons needed:

```shell
mkdir site_scons
git submodule -add -b vX.Y https://github.com/ncar/eol_scons site_scons/eol_scons
```

Omit `-b vX.Y` to get the latest version.

If the code repository is also on [NCAR github](https://github.com/ncar), then
the submodule can use a relative URL:

```shell
git submodule -add -b vX.Y ../eol_scons site_scons/eol_scons
git commit -am "Added eol_scons submodule vX.Y"
git push
```

Use `git clone --recurse-submodules` when cloning the repo to create the
`eol_scons` clone also.

### Use --site-dir

The `SCons` command line option `--site-dir` can be used to add `eol_scons` to
the `SCons` environment.  Specify the full path to the top of the `eol_scons`
source tree to add the `eol_scons` package to the Python path. However,
`eol_scons` will print the message below:

````sh
*** Importing from site_scons/eol_scons has been deprecated.
*** The repository should be a subdirectory of site_scons named eol_scons.
````

This message can be avoided using one of the other options, or it can be
safely ignored.

## Python Documentation

There is an attempt at generating HTML documentation from the python modules
using `doxygen`.  Run `doxygen` with the `docs` alias:

```shell
scons docs
```

The output is in `doxy/html/index.html`.
