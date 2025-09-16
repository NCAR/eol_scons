#! /usr/bin/env python3
# check for library paths missed by macdeployqt in installers
import os
import argparse
import glob
import subprocess
import shutil
from pathlib import Path


class AppBundleChecker:

    def __init__(self):
        # Get command line arguments
        args = self.parse_args()
        self.app_path = os.path.join(os.getcwd(), args.app)

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
        brew_prefix = args.brew_prefix
        if not brew_prefix:
            brew_prefix = "/opt/homebrew"
            if not (os.path.exists(brew_prefix)):
                brew_prefix = "/usr/local"
        self.homebrew_path = brew_prefix + '/opt'

    def parse_args(self):
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
                print("\nfound bad library path", line,
                      "referenced from:", path)
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
        if not (self.exists_in_app(library_name)):
            # need to add library file and update its self references
            if '.framework' in library_name:
                self.add_framework_to_app(library_name)
            else:
                self.add_library_to_app(library_name)
        # always need to update reference
        print("Updating reference: ", library_name)
        subprocess.run(["install_name_tool", "-change", library_path,
                        "@executable_path/../Frameworks/" + library_name,
                        referenced_from])

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

    def add_framework_to_app(self, framework_name):
        framework_dir = Path(framework_name).parts[0]
        print("adding missing framework to app bundle: ", framework_dir)
        # assume first result is fine
        src = self.find_file(framework_dir)
        # copy into frameworks dir
        try:
            # preserve symlinks within framework
            shutil.copytree(src, os.path.join(self.frameworks_path,
                                              framework_dir), symlinks=True)
        except NotADirectoryError:
            print(src, " is not a framework")
        new_framework_path = os.path.join(self.frameworks_path, framework_name)
        self.update_self_references(framework_name, new_framework_path, src)

    def find_file(self, name):
        # find file in local homebrew installation
        res = glob.glob("**/" + name, root_dir=self.homebrew_path,
                        recursive=True)
        return os.path.join(self.homebrew_path, res[0])

    def update_self_references(self, name, new_path, old_path):
        # update ID and self-reference of a file that has just been added to
        # the app bundle
        # update ID of file just copied
        subprocess.run(["install_name_tool", "-id",
                        "@executable_path/../Frameworks/" + name,
                        new_path])
        # update self-reference of file just copied
        subprocess.run(["install_name_tool", "-change", old_path,
                        "@executable_path/../Frameworks/" + name,
                        new_path])


def main():
    checker = AppBundleChecker()
    checker.check()


if __name__ == "__main__":
    main()
