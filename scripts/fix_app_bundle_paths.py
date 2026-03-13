#! /usr/bin/env python3
# check for library paths missed by macdeployqt in installers
import os
import argparse
import glob
import subprocess
import shutil
from pathlib import Path


class AppBundleChecker:

    def __init__(self, app, brew_prefix=None, app_path_override=False):
        if app_path_override:
            # supply exact app path to check, and use its directory directly
            # for all dependencies.
            app_path = os.path.dirname(app)
            self.app_path = app_path
            self.frameworks_path = app_path
            self.plugins_path = app_path
            # assuming only file present yet is the executable
            self.executable_path = app
        else:
            self.app_path = os.path.join(os.getcwd(), app)
            # Determine the exectutable to check
            files = os.listdir(os.path.join(self.app_path, 'Contents/MacOS'))
            # assumes only one executable in MacOS dir, which I think is standard
            # for mac apps
            self.executable_path = os.path.join(self.app_path, 'Contents/MacOS',
                                                files[0])
            # Set the frameworks path
            self.frameworks_path = os.path.join(self.app_path,
                                                "Contents/Frameworks")
            # Set the plugins path
            self.plugins_path = os.path.join(self.app_path,
                                            "Contents/PlugIns")

        # Find the homebrew path
        if not brew_prefix:
            brew_prefix = "/opt/homebrew"
            if not (os.path.exists(brew_prefix)):
                brew_prefix = "/usr/local"
        self.homebrew_path = brew_prefix + '/opt'

    def check(self):
        # check app itself
        self.check_executable(self.executable_path)

        # check all dylibs in frameworks path
        dylibs = glob.glob(self.frameworks_path + "/*.dylib")
        for d in dylibs:
            self.check_executable(d)

        # check all dylibs in plugins path
        plugins = glob.glob(self.plugins_path + "/*/*.dylib")
        for p in plugins:
            self.check_executable(p)

        # check all frameworks in frameworks path
        frameworks = glob.glob(self.frameworks_path + "/*.framework")
        for f in frameworks:
            self.check_framework(f)
        # Check if QtDBus exists in frameworks dir and warn user (for now)
        if not (self.exists_in_app("QtDBus.framework")):
            print("\n**Warning: QtDBus.framework does not exist. If you are " +
                  "codesigning this app you will need to manually add it.**\n")
        else:
            # QtDBus is present, so check its executable too
            dbus = glob.glob(self.frameworks_path + "/QtDBus.framework")
            self.check_framework(dbus[0])

    def check_executable(self, path):
        # run otool; find and fix any bad library paths
        result = subprocess.run(["otool", "-L", path], capture_output=True,
                                text=True)
        for line in result.stdout.splitlines()[1:]:  # first line is filename
            # remove preceding whitespace; get pathname w/o compatibility info
            line = line.split()[0]
            # good paths start with:
            # - @executable_path - macdeployqt has correctly updated path
            # - /usr/lib or /System/Library/Frameworks - assume these will be
            #   present on all user systems
            if not (line.startswith("@executable_path")
                    or line.startswith("/usr/lib")
                    or line.startswith("/System/Library/Frameworks")):
                self.fix_library_path(line, path)

    def check_framework(self, path):
        # create the name of the dylib inside the framework. this currently
        # assumes that the true path to the dylib (e.g.
        # Framework.framework/Versions/A/Framework) is symlinked to
        # Framework.framework/Framework.
        fname = os.path.basename(path).replace(".framework", "")
        dylib = os.path.join(path, fname)
        self.check_executable(dylib)

    def fix_library_path(self, library_path, referenced_from):
        if '.framework' in library_path:
            # assume the path is like Framework.framework/Versions/A/Framework
            # we want to preserve from the  *.framework on
            library_name = str(Path(*Path(library_path).parts[-4:]))
        else:
            library_name = os.path.basename(library_path)
        try:
            if not (self.exists_in_app(library_name)):
                # need to add library file and update its self references
                if '.framework' in library_name:
                    self.add_framework_to_app(library_name)
                else:
                    self.add_library_to_app(library_name)
            # always need to update reference
            print("Updating reference: ", library_name)
            new_library_path = self.get_new_library_path()
            self._install_name_tool("-change", library_path,
                                    new_library_path + library_name,
                                    referenced_from)
        except Exception:
            print("\nfound bad library path", library_path,
                  "referenced from:", referenced_from)
            raise

    def exists_in_app(self, lib):
        # check if dylib in frameworks path
        return os.path.exists(os.path.join(self.frameworks_path, lib))

    def add_library_to_app(self, library_name):
        # first have to find where file is in system - assume in homebrew
        print("adding missing library to app bundle: ", library_name)
        src = self.find_file(library_name)
        # copy into frameworks dir
        try:
            shutil.copy(src, self.frameworks_path)
        except IsADirectoryError:
            print(src, " is a framework")
        new_library_path = self.frameworks_path + "/" + library_name
        self.update_self_references(library_name, new_library_path, src)
        # if this library just got added, run check_executable on it too
        self.check_executable(new_library_path)

    def add_framework_to_app(self, framework_name):
        framework_dir = Path(framework_name).parts[0]
        print("adding missing framework to app bundle: ", framework_dir)
        # assume first result is fine
        src = self.find_file(framework_dir)
        # copy into frameworks dir
        fw_dest = os.path.join(self.frameworks_path, framework_dir)
        try:
            # Remove any existing flat-structured copy left by macdeployqt
            # before copying the full Versions/A layout from Homebrew.
            if os.path.exists(fw_dest):
                shutil.rmtree(fw_dest)
            # preserve symlinks within framework
            shutil.copytree(src, fw_dest, symlinks=True)
        except NotADirectoryError:
            print(src, " is not a framework")
        new_framework_path = os.path.join(self.frameworks_path, framework_name)
        self.update_self_references(framework_name, new_framework_path, src)

    def find_file(self, name):
        # find file in local homebrew installation
        res = glob.glob("**/" + name, root_dir=self.homebrew_path,
                        recursive=True)
        # Prefer kegs without explicit version markers (e.g. 'qt' before
        # 'qt@5', 'qt6') so the default generation is used.  glob returns
        # results in alphabetical order and 'qt@5' sorts before 'qt', so
        # without this sort the wrong Qt generation can be picked up, causing
        # framework layout mismatches (Versions/5/ vs Versions/A/).
        res.sort(key=lambda p:
                 sum(1 for c in p.split('/')[0] if c == '@' or c.isdigit()))
        return os.path.join(self.homebrew_path, res[0])

    @staticmethod
    def _install_name_tool(*args):
        # Suppress the "will invalidate the code signature" warning: it is
        # always expected when rewriting load commands in deployed binaries,
        # and the bundle will be re-signed as a separate step afterwards.
        result = subprocess.run(["install_name_tool"] + list(args),
                                capture_output=True, text=True)
        filtered = [line for line in result.stderr.splitlines()
                    if "invalidate the code signature" not in line]
        if filtered:
            print('\n'.join(filtered))

    def update_self_references(self, name, new_path, old_path):
        # update ID and self-reference of a file that has just been added to
        # the app bundle
        # update ID of file just copied
        new_library_path = self.get_new_library_path()
        self._install_name_tool("-id", new_library_path + name, new_path)
        # update self-reference of file just copied
        self._install_name_tool("-change", old_path,
                                new_library_path + name, new_path)
                        
    def get_new_library_path(self):
        new_library_path = "@executable_path/../Frameworks/"
        if self.frameworks_path == self.app_path:  # no app bundle structure
            new_library_path = "@executable_path/"
        return new_library_path

def parse_args():
    """ Instantiate a command line argument parser """

    # Define command line arguments which can be provided
    parser = argparse.ArgumentParser(
        description="Check for Library paths missed by macdeployqt in" +
        "MAC .app bundles")
    parser.add_argument(
        '--app', type=str, required=True,
        help='relative path to .app bundle')
    parser.add_argument('--brew_prefix', type=str, default=None, help="homebrew prefix")

    # Parse the command line arguments
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    checker = AppBundleChecker(args.app, args.brew_prefix)
    checker.check()


if __name__ == "__main__":
    main()
