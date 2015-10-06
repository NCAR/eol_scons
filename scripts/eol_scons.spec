%define name eol_scons

Summary: EOL SCons tools
Name: %{name}
Version: %{version}
Release: %{release}
License: GPL
Group: System Environment/Daemons
Url: http://www.eol.ucar.edu/
Packager: Gordon Maclean <maclean@ucar.edu>
Vendor: UCAR
BuildArch: noarch
Requires: scons
BuildRequires: python-devel
Source: %{name}-%{version}.tar.gz

%description
EOL SCons tools

%prep
%setup -n eol_scons

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/usr/share/scons/site_scons/eol_scons
cp -r . $RPM_BUILD_ROOT/usr/share/scons/site_scons/eol_scons

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/share/scons/site_scons/eol_scons

%changelog
* Wed Sep 02 2015 Gordon Maclean <maclean@ucar.edu> 1.0-1
- Initial
