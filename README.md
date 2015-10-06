# eol_scons

## Installing eol_scons

SCons version 2.3 searches in the following locations for python packages (see the documentation for the --site-dir command line option):

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

Therefore one needs to install eol_scons in one of the above places.

If you're using a version of SCons prior to version 2.3, you must install eol_scons in ./site_scons, in the same directory as your SConstruct.

Another option is to create an eol_scons Python package and install it in the usual locations. Support for this should be provided soon. Note that SCons ignores the PYTHONPATH environment variable.

### Install eol_scons to /usr/share/scons/site_scons on RedHat Linux systems
An eol_scons RPM is found in the EOL RPM repository, which installs eol_scons to /usr/share/scon/site_scons.

Enable the EOL yum repository on RHEL systems:
    sudo rpm -ihv \
        http://www.eol.ucar.edu/software/rpms/eol-repo-epel-1-3.noarch.rpm
Enable the EOL yum repository on Fedora systems:
    sudo rpm -ihv \
        http://www.eol.ucar.edu/software/rpms/eol-repo-fedora-1-3.noarch.rpm

Install eol_scons:
    sudo yum install eol_scons
or on newer Fedora systems:
    sudo dnf install eol_scons
 
### Install eol_scons to $HOME/.scons/site_scons

    mkdir -p $HOME/.scons
    cd $HOME/.scons
    git clone http://github.com/ncareol/eol_scons site_scons

### Install eol_scons to ./site_scons
In the directory containing SConstruct:

    git clone http://github.com/ncareol/eol_scons site_scons


## Using eol_scons
In your SConstruct file, simply import eol_scons. The import will add eol_scons/tools to the SCons tool search path:

    import eol_scons
    env = Environment(tools=['default','boost_date_time'])

