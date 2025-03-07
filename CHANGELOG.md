# CHANGELOG

## [Unreleased] - Unreleased

## [4.3] - Pending

- Fix `ninja` tool conflict which started with SCons 4.9.0, causing error
  messages like `no attribute 'NinjaCheck'`.  The `ninja` tool name is now an
  alias for the renamed tool file `ninja_es.py`.
- fix boost_thread tool to cache libs after first configure check
- try to optimize how added methods are called to improve speed and debug
  tracing
- use a global cache for pkg-config results, rather than per-Environment,
  presuming that all Environments in the same build will want to use the same
  settings for pkg-config dependencies
- the deprecated file-backed-store for VariableCache has been removed, and now
  VariableCache works to cache variables globally, especially for the Qt tool
- eol_scons can now be installed as a python package from source, in
  particular to create a scons build environment with `pipenv` that does not
  require a `site_scons` directory.  See [README.md](README.md).
- relicense as MIT, update copyright info everywhere
- make tests more robust on platforms with different package installations
- prevent build_rpms from listing debug packages when disabled
- fix staticlink.py tool when LIBPATH is not set: fixes error message
  `NoneType object is not subscriptable trying to evaluate
  ${_replace_static_libraries(__env__)}`
- many obsolete and (presumed) unused tools have been removed
- gcc.py tool: Sanitized output no longer needs to be translated, so
  AsanFilter() has been removed.  See gcc.py for details.
- testing.py tool: simplify SpawnerLogger and LogAction and make their
  arguments more consistent, but the changes are not backwards compatible and
  could change the console output.  SpawnerLogger is now in its own module,
  eol_scons.spawner, and will accumulate all output when multiple actions are
  spawned by it.
- refactor testing to use less shell script and more pytest
- eol_scons_tool.py is now in its own site_tools directory

## [4.2.5] - 2023-12-13

- `git clean` copied source directories before archiving them
- fix `build_rpm.sh` to work when `SConstruct` is not in the top directory
- add _errors_ to `buildmode` to add `-Werror` flag
- skip netcdf configure checks if pkg-config succeeds
- cache Qt5 check rather than repeating it over and over
- remove support for xerces-c 2.7
- fix key error in nidas tool when LIBS not set

## [4.2.4] - 2023-09-02

- canfestival support for API-only when python2 not available
- `QtUiPlugin` now a recognized Qt5 tool.
- Fixes for Qt and other tools on Ubuntu.
- Changes in library discovery on Darwin.
- Use `PrintProgress` for kmake messages so they can be suppressed with -Q.

## [4.2.3] - 2022-12-15

- Keep `build_rpm.sh` working with spec files which use `%setup -n <pkgname>`.

## [4.2.2] - 2022-12-10

- `build_rpm.sh` removes scons artifacts left over from a source copy or from
  the _versionfiles_ target.
- Debian packaging cleans compiled python and now installs the python package
  into the new location `site_scons/eol_scons/eol_scons`.
- `build_rpm.sh` now has a _test_ method to stage the source archive from a
  hard linked copy of the source repo instead of a clone.  The source archive
  directory now has the conventional name `{name}-{version}`, so `%setup`
  macros no longer need the `-n` option.

## [4.2.1] - 2022-08-30

### Fixed

- In the `Install()` method which adds the automatic install alias, restore
  the resolution of the destination as a directory node before passing the
  destination along as string path.  This forces variables to be interpolated
  when the builder is created, since some projects have relied on that.

### Added

- `build_rpm.sh` can create snapshot packages from untagged source using the
  commit hash as the version identifier.  It bumps a copy of the spec file to
  a new version with the commit hash embedded, then the rest of the rpm build
  works as before.  In particular the specific source version to be packaged
  is extracted from the version in the spec file.  The spec changelog is
  technically not quite correct because it only contains a single new entry
  for the snapshot being created, it does not mention if there were any
  snapshots prior to it.
  
  Example:

  ```sh
  scons build_rpm scripts/eol_scons.spec snapshot
  ```

  The primary purpose is to test packaging for the latest commit without
  requiring a tag, but it could also allow projects to release rolling package
  snapshots if desired, since the generated package versions should order
  correctly.  The packages are still only built from clean source checkouts.

## [4.2] - 2022-08-26

### Added

- The `eol_scons` source now has its own `SConstruct` for installing files to
  a directory specified by the `PREFIX` variable.
- Scripts can now be shared and executed through the `eol_scons` package.
  Call `eol_scons.RunScripts()` to look for known script names on the command
  line, and if found, execute the script with any succeeding arguments.  So
  far the only script is `build_rpm`.  New scripts can be added easily, but
  they cannot require single-hyphen arguments, since those will be handled by
  scons.  Scripts can use words or double-hyphen options.  Example:

  ```sh
  $ scons -Q build_rpm scripts/eol_scons.spec rpms
  /home/granger/rpmbuild_piglet/SRPMS/eol_scons-4.2~alpha2-1.fc35.src.rpm
  /home/granger/rpmbuild_piglet/RPMS/noarch/eol_scons-4.2~alpha2-1.fc35.noarch.rpm
  ```

- Help option `-h --list-installs` prints all targets in `FindInstalledFiles()`.
- Some messages printed by eol_scons, especially the initial boilerplate about
  loading configs, can now be suppressed with the SCons `-Q` (*no_progress*)
  option.  SConscript files and tools can call the `PrintProgress()` method to
  print messages which should be suppressed by `-Q`.

### Tool changes: gitinfo

- Add `gitinfo` variable.  When set to `off`, the `gitinfo` tool will try
  to load repo version info from a generated header instead of running
  `git` tools.  This allows builds in source archives to use the repo
  version info, like for RPM packages.
- Add `gitdump` target.  For each directory where the `gitinfo` tool collects
  repo info, there is a target which prints the repo info.  The target must be
  named on the command-line, like `scons ./gitdump`.
- All `gitinfo` targets are added to a `versionfiles` alias, so generic
  scripts can generate all versioned output with `scons versionfiles`.  There
  is also a no-op for the `versionfiles` alias, so `scons versionfiles` does
  not cause an error on projects which do not use `gitinfo`.

### Changed

- The eol_scons override of the `Install()` method can be disabled by calling
  `eol_scons.EnableInstallAlias(False)`.  It still defaults to enabled, but
  someday could be deprecated.  This allows projects to choose different
  install aliases, like *install* and *install.root* and *install.doc*.  There
  was also a change to allow the `Install()` override to work with the
  standard SCons option `--install-sandbox`.
- Consolidate the `buildmode` settings into the single tool rather than
  providing separate tools for `warnings`, `debug`, and so on.  This fixes a
  problem with SCons 4.4 where a python built-in module actually tries to
  import `warnings`.

### Deprecated

- eol_scons should now be installed as a subdirectory of site_scons.  Prior to
  this, the eol_scons repository was typically cloned into `~/.scons` and
  named `site_scons`, or else it was added to a project as a git submodule
  named `site_scons`.  This practice interferes with adding other SCons
  extensions under the `site_scons` directory, and it is confusing that the
  repository is cloned with a different name.  Now the `site_scons` directory
  must be created first, either as part of the project or in `~/.scons`, then
  the eol_scons repository can be cloned into that directory with the name
  `eol_scons`.  The new `__init__.py` file in the top directory takes care of
  adding the `eol_scons/eol_scons` directory to the path of the `eol_scons`
  package.  Importing `eol_scons` using the old scheme prints a deprecation
  message.
- eol_scons now requires Python 3.6.  SCons 4.0 requires Python 3.5, SCons 4.4
  requires Python 3.6, so eol_scons is following suit.  The biggest known
  issue with this is that on RHEL7 the default python and scons is still
  python 2.7.  There is a scons package based on python3, `python36-scons`,
  but it must be invoked as `scons-3`.  The RPM spec has been updated to force
  byte compiling with python3 with an install dependency on `scons-python3`.

### Removed

- Remove runtime ld path (-R link option) in many places, partly to facilitate
  MacOS builds.

## [4.1] - 2021-01-25

- Refactor for Qt5 modules, providing tools named after the module which apply
  that module for the project Qt version.
- In prefixoptions tool, make sure optional extra search paths are always
  added last to `CPPPATH` and `LIBPATH`.
- Port to SCons 4.1, removing use of `SCons.Warnings.Warning`.
- Add `jsoncpp` tool.

## [3.0] - 2017-12-21

- Port to SCons 3.0 and python 3.

## [2.9] - 2017-12-18

- last tagged release before scons 3.0 port

## [2.0] - 2015-10-05

- first tagged release

<!-- Versions -->
[unreleased]: https://github.com/NCAR/eol_scons
[4.3]: https://github.com/NCAR/eol_scons/compare/v4.2.5...v4.3
[4.2.5]: https://github.com/NCAR/eol_scons/compare/v4.2.4...v4.2.5
[4.2.4]: https://github.com/NCAR/eol_scons/compare/v4.2.3...v4.2.4
[4.2.3]: https://github.com/NCAR/eol_scons/compare/v4.2.2...v4.2.3
[4.2.2]: https://github.com/NCAR/eol_scons/compare/v4.2.1...v4.2.2
[4.2.1]: https://github.com/NCAR/eol_scons/compare/v4.2...v4.2.1
[4.2]: https://github.com/NCAR/eol_scons/compare/v4.1...v4.2
[4.1]: https://github.com/NCAR/eol_scons/compare/v3.0...v4.1
[3.0]: https://github.com/NCAR/eol_scons/compare/v2.9...v3.0
[2.9]: https://github.com/NCAR/eol_scons/compare/v2.0...v2.9
[2.0]: https://github.com/NCAR/eol_scons/releases/tag/v2.0
