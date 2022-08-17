# Changelog

Changelog for eol_scons.

## [Unreleased]

- Add `gitinfo` variable.  When set to `off`, the `gitinfo` tool will try to
  load repo version info from a generated header instead of running `git`
  tools.
- Add `gitdump` target.  For each directory where the `gitinfo` tool collects
  repo info, there is a target which prints the repo info.  The target must be
  named on the command-line, like `scons ./gitdump`.
- The eol_scons override of the `Install()` method can be disabled by calling
  `eol_scons.EnableInstallAlias(False)`.  It still defaults to enabled, but
  someday could be deprecated.  This allows projects to choose different
  install aliases, like _install_ and _install.root_ and _install.doc_.  The
  `Install()` override now works better with the standard SCons option
  `--install-sandbox`.
- Consolidate the `buildmode` settings into the single tool rather than
  providing separate tools for `warnings`, `debug`, and so on.  This fixes a
  problem with SCons 4.4 where a python built-in module actually tries to
  import `warnings`.
- Remove runtime ld path (-R link option) in many places, partly to facilitate
  MacOS builds.
- Print all targets in `FindInstalledFiles()` with `-h --list-installs`.
- Some messages printed by eol_scons, especially the initial boilerplate about
  loading configs, can now be suppressed with the SCons `-Q` (*no_progress*)
  option.  SConscript files and tools can use the `PrintProgress()` method to
  print messages which should be suppressed by `-Q`.

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
[unreleased]: https://github.com/NCAR/eol_scons/compare/v4.1...HEAD
[4.1]: https://github.com/NCAR/eol_scons/compare/v3.0...v4.1
[3.0]: https://github.com/NCAR/eol_scons/compare/v2.9...v3.0
[2.9]: https://github.com/NCAR/eol_scons/compare/v2.0...v2.9
[2.0]: https://github.com/NCAR/eol_scons/releases/tag/v2.0
