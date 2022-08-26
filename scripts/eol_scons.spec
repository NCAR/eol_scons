%define name eol_scons
%define __python /usr/bin/python3

Summary: EOL SCons tools
Name: %{name}
Version: 4.2~alpha2
Release: 1%{?dist}
License: GPL
Group: System Environment/Daemons
Url: http://www.eol.ucar.edu/
Packager: Gordon Maclean <maclean@ucar.edu>
Vendor: UCAR
BuildArch: noarch

Requires: scons-python3
BuildRequires: python3-devel scons-python3
Source: %{name}-%{version}.tar.gz

%description
EOL SCons tools

%prep
%setup -n eol_scons

%build

%install
rm -rf $RPM_BUILD_ROOT
scons --install-sandbox $RPM_BUILD_ROOT PREFIX=/usr/share/scons/site_scons install

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/share/scons/site_scons/eol_scons

%changelog
* Fri Aug 26 2022 Gary Granger <granger@ucar.edu> - 4.2~alpha2-1
- build v4.2-alpha2

