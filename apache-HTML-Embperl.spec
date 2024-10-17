%define module HTML-Embperl
%define mod_conf 76_Embperl.conf

Summary:	Framework for building web sites with Perl
Name:		apache-%{module}
Version:	2.4.0
Release:	3
License:	GPL
Group:		System/Servers
URL:		https://perl.apache.org/embperl/
Source0:	ftp://ftp.dev.ecos.de/pub/perl/embperl/Embperl-%{version}.tar.gz
Source1:	%{mod_conf}
Patch0:		Embperl-2.09b-fix-CVS.patch
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.0
Requires(pre):	apache >= 2.2.0
Requires:	apache-mod_perl >= 1:2.0.2
BuildRequires:	apache >= 2.2.0
BuildRequires:	apache-devel >= 2.2.0
BuildRequires:	apache-modules >= 2.2.0
BuildRequires:	apache-mod_perl >= 1:2.0.2
BuildRequires:	apache-mod_perl-devel >= 1:2.0.2
BuildRequires:	libxml2-devel
BuildRequires:	libxslt-devel
BuildRequires:	perl-Apache-Session
BuildRequires:	perl-Apache-SessionX 
BuildRequires:	perl-ExtUtils-XSBuilder
BuildRequires:	perl-HTML-Parser 
BuildRequires:	perl-Parse-RecDescent
BuildRequires:	perl-Tie-IxHash
BuildRequires:	perl-libwww-perl
BuildRequires:	perl-devel
BuildRequires:	file
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

%description
Embperl is a framework for building websites with Perl.

For the beginner it's an easy to setup and use way of embedding Perl code in
HTML pages. It delivers several features that ease the task of creating a
ebsites, including dynamic tables, formfield-processing,
escaping/unescaping, session handling, caching and more.

If your demands grow it gives you the power to make your Website
object-oriented and build it out of small reusable components. If you don't
like the idea of mixing up all your layout and code then Embperl also
supports separating it in different objects (e.g. creating an MVC
application). Of course Embperl doesn't tie you to HTML - it allows
components to be from different source formats (e.g. HTML, WML, XML, POD,
...) and if necessary transforms them (for example via XSLT) to other output
formats. This is achieved by dividing the output generation into small
steps, where each is processed by a plugable provider. Advanced users can
create their own syntax definitions (for example tag libraries) and extend
Embperl by writing their own providers and much more...

Embperl is a server-side tool, which means that it's browser-independent. It
can run in various ways: under mod_perl, as a CGI script, or offline.

%prep

%setup -q -n Embperl-%{version}

cp %{SOURCE1} %{mod_conf}

# fix strange perms
find . -type d -perm 0700 -exec chmod 755 {} \;
find . -type f -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0444 -exec chmod 644 {} \;

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

rm -f eg/x/config.htm

%patch0 -p1

perl -pi -e "s/\&lt;/\</;" eg/x/loop.htm

cat << EOF > eg/.htaccess
<Files ~ (\.htm)>
SetHandler perl-script
PerlResponseHandler Embperl
</Files>
Options +Indexes
EOF

find -type d|grep CVS|xargs rm -rf
find -type f|grep cvsignore|xargs rm -f

%build
# (oe) pull in the apr and apu headers where ever they may be
export APR_HEADERS="`apr-1-config --includes`"
export APU_HEADERS="`apu-1-config --includes`"
perl -pi -e "s|-I\\\$EPPATH \\\$i|-I\\\$EPPATH \\\$i $APR_HEADERS $APU_HEADERS|g" Makefile.PL

perl -pi -e "s/action_module/actions_module/;" Makefile.PL
perl xsbuilder/source_scan.pl
perl xsbuilder/xs_generate.pl

cat << EOF | perl Makefile.PL INSTALLDIRS=vendor OPTIMIZE="%{optflags} `apr-1-config --cppflags`" INC="-I%{_includedir}/apache -I%{_includedir}/apache/regex -I%{_includedir}/apache/os/unix $APR_HEADERS $APU_HEADERS -I%{_includedir}/libxml2 -I./xs" 
y
%{_includedir}/apache
y
%{_sbindir}/httpd
%{_libdir}/apache-extramodules
%{_libdir}/apache
.
EOF

make LD_RUN_PATH=""

# one test fails atm
#make test

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

eval `perl '-V:installarchlib'`
install -d %{buildroot}/$installarchlib
%makeinstall_std

%__os_install_post
find %{buildroot}%{_prefix} -type f -print | sed "s@^%{buildroot}@@g" | grep -v perllocal.pod > %{module}-%{version}-filelist

install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

install -d %{buildroot}%{_var}/www/html/addon-modules
ln -s ../../../..%{_docdir}/%{name}-%{version} %{buildroot}%{_var}/www/html/addon-modules/%{name}-%{version}

rm -rf test/tmp/* 
rm -rf blib
mkdir -p blib/arch
pushd blib/arch
eval `perl '-V:vendorarch'`
ln -s ../../../../../..$vendorarch/auto/ .
popd

cd test
#chmod 755 tmp
find -type f|xargs perl -pi -e \
	"s|%{_builddir}/embperl|%{_docdir}/%{name}-%{version}|g;"
perl -pi -e 's/\015//;' conf/config.pl
cd ..
rm -f %{buildroot}$vendorarch/auto/Embperl/*.bs

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean 
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc MANIFEST READM* eg test.pl test *.pod TODO blib
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_bindir}/*
%{perl_vendorlib}/*
%{_mandir}/*/*
%{_var}/www/html/addon-modules/*


%changelog
* Wed Jan 25 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 2.4.0-2
+ Revision: 768358
- svn commit -m mass rebuild of perl extension against perl 5.14.2

* Sun Oct 17 2010 Oden Eriksson <oeriksson@mandriva.com> 2.4.0-1mdv2011.0
+ Revision: 586360
- 2.4.0

* Tue Sep 01 2009 Thierry Vignaud <tv@mandriva.org> 2.2.0-8mdv2010.0
+ Revision: 423982
- rebuild

* Thu Jun 19 2008 Thierry Vignaud <tv@mandriva.org> 2.2.0-7mdv2009.0
+ Revision: 226157
- rebuild

* Mon Feb 18 2008 Thierry Vignaud <tv@mandriva.org> 2.2.0-6mdv2008.1
+ Revision: 170700
- rebuild
- fix "foobar is blabla" summary (=> "blabla") so that it looks nice in rpmdrake

* Tue Jan 15 2008 Thierry Vignaud <tv@mandriva.org> 2.2.0-5mdv2008.1
+ Revision: 152438
- rebuild
- rebuild
- kill re-definition of %%buildroot on Pixel's request

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

* Sun Sep 09 2007 Oden Eriksson <oeriksson@mandriva.com> 2.2.0-3mdv2008.0
+ Revision: 83747
- rebuild


* Sun Mar 11 2007 Oden Eriksson <oeriksson@mandriva.com> 2.2.0-2mdv2007.1
+ Revision: 141325
- rebuild

* Thu Nov 09 2006 Oden Eriksson <oeriksson@mandriva.com> 2.2.0-1mdv2007.1
+ Revision: 79302
- Import apache-HTML-Embperl

* Tue Apr 11 2006 Oden Eriksson <oeriksson@mandriva.com> 2.2.0-1mdk
- Minor feature enhancements
- drop upstream patches; P1
- zero out LD_RUN_PATH to fix rpath

* Tue Jan 31 2006 Oden Eriksson <oeriksson@mandriva.com> 2.1.0-1mdk
- 2.1.0
- added P1 to make it build against apache-2.2.0
- fix versioning

* Tue Oct 04 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.1-1mdk
- 2.0.1 (Minor bugfixes)
- run the test suite

* Tue Aug 16 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0.0-1mdk
- 2.0.0 (Major feature enhancements)

* Mon Aug 15 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0-0.rc5.1mdk
- 2.0 rc5

* Fri Jun 03 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_2.0-0.rc3.1mdk
- 2.0 rc3
- rename the package
- the conf.d directory is renamed to modules.d
- use new rpm-4.4.x pre,post magic

* Sun Mar 20 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0-0.rc1.6mdk
- remove broken perl version detection, rely on autodetection instead

* Sun Mar 20 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0-0.rc1.5mdk
- use the %%mkrel macro

* Mon Feb 28 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0-0.rc1.4mdk
- fix %%post and %%postun to prevent double restarts

* Thu Feb 24 2005 Stefan van der Eijk <stefan@eijk.nu> 2.0.53_2.0-0.rc1.3mdk
- fix bug #6574

* Wed Feb 16 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0-0.rc1.2mdk
- spec file cleanups, remove the ADVX-build stuff

* Wed Feb 09 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_2.0-0.rc1.1mdk
- built for apache 2.0.53

* Fri Jan 21 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0-0.rc1.2mdk
- rebuilt for latest mod_perl

* Tue Nov 30 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0-0.rc1.1mdk
- rebuilt for perl-5.8.6
- fix version

* Wed Sep 29 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_2.0rc1-1mdk
- built for apache 2.0.52

* Fri Sep 17 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.51_2.0rc1-1mdk
- built for apache 2.0.51

* Thu Aug 26 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0rc1-0.1mdk
- 2.0rc1

* Tue Aug 03 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0b12-0.20040801.1mdk
- use a recent snap (20040801)

* Tue Aug 03 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0b11-1mdk
- 2.0b11
- remove redundant provides
- pull in the apr and apu headers where ever they may be

* Thu Apr 08 2004 Michael Scherer <misc@mandrake.org> 2.0b9-0.20030308.8mdk 
- rebuild for new perl

