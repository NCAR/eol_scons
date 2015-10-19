# eol_scons

## Installing eol_scons

SCons version 2.3 searches in the following locations for python packages, where ./site_scons is in the same directory as the SConstruct file. See the documentation for the --site-dir command line option:

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

Therefore one needs to install eol_scons in one of the above places, or specify a --site-dir command line option.

SCons prior to version 2.3 only searches ./site_scons.

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
git clone http://github.com/ncareol/eol_scons site_scons
```

Or if you have setup an ssh key on github, and will want to push back your changes to github:
```shell
git clone git@github.com:ncareol/eol_scons.git site_scons
```

### Install eol_scons to ./site_scons
In the directory containing SConstruct:
```shell
git clone http://github.com/ncareol/eol_scons site_scons
```
or
```shell
git clone git@github.com:ncareol/eol_scons.git site_scons
```

## Using eol_scons
In your SConstruct file, simply import eol_scons. The import will add eol_scons/tools to the SCons tool search path:
```python
import eol_scons
env = Environment(tools=['default','boost_date_time'])
```

