# README eol_scons

## Updates

See [CHANGELOG.md](CHANGELOG.md) for changes.

## Installing eol_scons

By default, SCons looks for extensions and additional tools in _site
directories_ named `site_scons`.  The standard locations for different
platforms are listed in the documentation for the `--site-dir` command line
option on the [SCons man
page](https://scons.org/doc/production/HTML/scons-man.html). On all platforms,
the site directory with the highest precedence is `./site_scons`, in the same
directory as the `SConstruct`.  Therefore, several different ways to add
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
`site_init.py` or `site_tools`, then `eol_scons` does not prevent it.
Further, there is a great deal of flexibility in installing `eol_scons` as a
python package instead of under a `site_scons` directory, since it can be
managed with all the common Python virtual environment tools, including `pip`
and `pipenv`.

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
other python dependencies, such as the `requests` package.

Of course the same approach can be used with `pip` to install `eol_scons` into
other python environments.

The source and wheel packages can be built like below, assuming the python
`build` package is installed in the current python environment.

```sh
python -m build
```

The resulting wheel in `./dist` can then be installed into a python virtual
environment, same as above.

### Install to $HOME/.scons/site_scons

In the past the eol_scons repository had to be cloned as the `site_scons`
subdirectory, but that has since been corrected.  Now `eol_scons` can be
cloned as itself under the `site_scons` directory, so that other SCons
extensions can be installed under `site_scons` also.

```shell
mkdir -p $HOME/.scons/site_scons
cd $HOME/.scons/site_scons
git clone https://github.com/ncar/eol_scons
```

### RPM for RedHat Linux systems

The RPM package installs eol_scons to `/usr/share/scons/site_scons`.  You may
be able to install the RPM for your system from the EOL yum repository.

Enable the EOL yum repository on RHEL systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-epel.noarch.rpm
```
  
or, on Fedora systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-fedora.noarch.rpm
```

Install RPM:

```shell
sudo yum install eol_scons
```

### Install from source to rpm path

To install eol_scons from source to the same location as the RPM package, use
this command:

```shell
scons PREFIX=/usr/share/scons/site_scons install
```

### Install to project site_scons

Create the `./site_scons` subdirectory in the directory containing `SConstruct`,
then clone `eol_scons` into it same as above.

### Access as a git submodule

In a git repository, in the same directory as your SConstruct, where vX.Y is
the tagged branch of eol_scons you want to use, or leave off the '-b vX.Y' if
you want the latest:

```shell
mkdir site_scons
git submodule -add -b vX.Y https://github.com/ncar/eol_scons site_scons/eol_scons
```

If your code repository is also on [NCAR github](https://github.com/ncar), you
can use a relative URL:

```shell
git submodule -add -b vX.Y ../eol_scons site_scons/eol_scons
```

Then

```shell
git commit -am "Added eol_scons submodule vX.Y"
git push ...
```

Use `git clone --recurse-submodules` when cloning the repo to create the
eol_scons clone also.

### Use --site-dir

The `SCons` command line option `--site-dir` can be used to add `eol_scons` to
the `SCons` environment.  You can provide the full path to the top of the
`eol_scons` source tree, since that will add the `eol_scons` package to the Python path.  However,
`eol_scons` will print the message below:

````sh
*** Importing from site_scons/eol_scons has been deprecated.
*** The repository should be a subdirectory of site_scons named eol_scons.
````

This message can be avoided using one of the other options, or it can be
safely ignored.

## Using eol_scons

In your SConstruct file, simply import eol_scons. The import will add
eol_scons/tools to the SCons tool search path:

```python
import eol_scons
env = Environment(tools=['default', 'boost_date_time'])
```

The import also modifies the SCons tool path so that every `Environment`
created with the `default` tool will automatically get the standard
`eol_scons` extensions.  A project can use that to make sure certain tools
("global tools") are applied to every `Environment`, without requiring the
tools be loaded explicitly everywhere.

## Documentation

See [this README](eol_scons/README) for an overview of how it works, though
that documentation is not necessarily up to date.

There is an attempt at generating HTML documentation from the python modules
and README files using `doxygen`.  Run `doxygen` with the `docs` alias:

```shell
scons docs
```

The output is in `doxy/html/index.html`.

Someday the README guide should be updated and converted to markdown.  Also,
some useful extensions to basic features especially need to be documented,
like how to add brief help for variables, and how to use help to list alias
and install targets.
