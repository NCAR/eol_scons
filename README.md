# README eol_scons

## Updates

See [CHANGELOG.md](CHANGELOG.md) for changes.

## Installing eol_scons

By default, SCons searches in the following locations for python packages,
where ./site_scons is in the same directory as the SConstruct file (see the
documentation for the SCons --site-dir command line option):

* Windows
  * %ALLUSERSPROFILE/Application Data/scons/site_scons
  * %USERPROFILE%/Local Settings/Application Data/scons/site_scons
  * %APPDATA%/scons/site_scons
  * %HOME%/.scons/site_scons
  * ./site_scons

* Mac OS X
  * /Library/Application Support/SCons/site_scons
  * /opt/local/share/scons/site_scons (for MacPorts)
  * /sw/share/scons/site_scons (for Fink)
  * $HOME/Library/Application Support/SCons/site_scons
  * $HOME/.scons/site_scons
  * ./site_scons

* Linux
  * /usr/share/scons/site_scons
  * $HOME/.scons/site_scons
  * ./site_scons

Therefore if eol_scons is not in one of the above places, you must use the
`--site-dir` command line option.

Another option is to create an eol_scons Python package and install it in the
usual locations. Note that SCons ignores the PYTHONPATH environment variable.

### RPM for RedHat Linux systems

To install eol_scons to /usr/share/scons/site_scons, you can install the RPM
from the EOL yum repository.

Enable the EOL yum repository on RHEL systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-epel-1-3.noarch.rpm
```
  
or, on Fedora systems:

```shell
sudo rpm -ihv http://www.eol.ucar.edu/software/rpms/eol-repo-fedora-1-3.noarch.rpm
```

Install RPM:

```shell
sudo yum install eol_scons
```

To install eol_scons from source to the same location as the package, use this
command:

```shell
scons PREFIX=/usr/share/scons/site_scons install
```

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

### Install to site_scons

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
