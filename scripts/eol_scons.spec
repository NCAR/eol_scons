%define name eol_scons
%define __python /usr/bin/python3

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

Requires: scons-python3
BuildRequires: python3-devel
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
