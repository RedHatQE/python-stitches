Name:		python-stitches
Version:	0.4
Release:	1%{?dist}
Summary:	Multihost actions toolbox

Group:		Development/Python
License:	GPLv3+
URL:		https://github.com/RedHatQE/python-stitches
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:  noarch

BuildRequires:	python-devel
Requires:	python-paramiko python-nose PyYAML python-plumbum python-rpyc

%description

%prep
%setup -q

%build

%install
%{__python} setup.py install -O1 --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc LICENSE README.md
%{python_sitelib}/*.egg-info
%{python_sitelib}/stitches/*.py*

%changelog
* Tue Jun 04 2013 Vitaly Kuznetsov <vitty@redhat.com> 0.4-1
- add disable_rpyc option (speed up) (vitty@redhat.com)
- connection.py: allow hostname-only connections (vitty@redhat.com)
- Add python-rpyc support (vitty@redhat.com)
* Thu Mar 14 2013 Vitaly Kuznetsov <vitty@redhat.com> 0.3-1
- 0.3

* Tue Dec 04 2012 Vitaly Kuznetsov <vitty@redhat.com> 0.2-1
- new package built with tito

