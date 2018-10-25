# eol_scons

## Updates

eol_scons has been ported to SCons 3.0 and Python 3, but it should remain
compatible with Python 2.7 and SCons 2, whatever versions are available on
CentOS as of 7.4.

## Installing eol_scons

By default, SCons searches in the following locations for python packages, where ./site_scons is in the same directory as the SConstruct file (see the documentation for the SCons --site-dir command line option):
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

* Solaris
   * /opt/sfw/scons/site_scons
   * /usr/share/scons/site_scons
   * $HOME/.scons/site_scons
   * ./site_scons

* Linux, HPUX, and other Posix-like systems
   * /usr/share/scons/site_scons
   * $HOME/.scons/site_scons
   * ./site_scons

Therefore one needs to install eol_scons in one of the above places, or use the --site-dir command line option.

Another option is to create an eol_scons Python package and install it in the usual locations. Support for this should be provided soon. Note that SCons ignores the PYTHONPATH environment variable.

### eol_scons RPM for RedHat Linux systems
To install eol_scons to /usr/share/scons/site_scons, you can install the RPM from the EOL yum repository.

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

### Install eol_scons to $HOME/.scons/site_scons
```shell
mkdir $HOME/.scons
cd $HOME/.scons
git clone http://github.com/ncar/eol_scons site_scons
```

Or if you have setup an ssh key on github, and will want to push back your changes to github:
```shell
git clone git@github.com:ncar/eol_scons.git site_scons
```

### Install eol_scons to ./site_scons
In the directory containing SConstruct:
```shell
git clone http://github.com/ncar/eol_scons site_scons
```
or
```shell
git clone git@github.com:ncar/eol_scons.git site_scons
```

### Access eol_scons as a git submodule
In a git repository, in the same directory as your SConstruct, where vX.Y is the tagged branch of eol_scons you want to use, or leave off the '-b vX.Y' if you want the latest:
```shell
git submodule -add -b vX.Y https://github.com/ncar/eol_scons site_scons
```
If your code repository is also on https://github.com/ncar, you can use a relative URL:
```shell
git submodule -add -b vX.Y ../eol_scons site_scons
```
Then
```
git commit -am "Added eol_scons submodule vX.Y"
git push ...
```
Remember to use --recursive when cloning your repo:
```shell
git clone --recursive
```

## Using eol_scons
In your SConstruct file, simply import eol_scons. The import will add eol_scons/tools to the SCons tool search path:
```python
import eol_scons
env = Environment(tools=['default','boost_date_time'])
```

