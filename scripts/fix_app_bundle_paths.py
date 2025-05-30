#! /usr/bin/env python3
# check for library paths missed by macdeployqt in installers
import os
import argparse
import glob
import subprocess
import shutil


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
        self.check_executable(self.executable_path)
        # check all dylibs in frameworks path
        dylibs = glob.glob(self.frameworks_path + "/*.dylib")
        for d in dylibs:
            self.check_executable(d)

        # Check if QtDBus exists in frameworks dir and warn user (for now)
        if not (self.exists_in_app("QtDBus.framework")):
            print("\n**Warning: QtDBus.framework does not exist. If you are " +
                  "codesigning this app you will need to manually add it.**\n")

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

    def fix_library_path(self, library_path, referenced_from):
        library_name = os.path.basename(library_path)
        if not (self.exists_in_app(library_name)):
            # need to add library file and update its self references
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
        res = glob.glob("**/" + library_name, root_dir=self.homebrew_path,
                        recursive=True)
        # assume first result is fine
        src = os.path.join(self.homebrew_path, res[0])
        # copy into frameworks dir
        shutil.copy(src, self.frameworks_path)
        # update ID of file just copied
        new_library_path = self.frameworks_path + "/" + library_name
        subprocess.run(["install_name_tool", "-id",
                        "@executable_path/../Frameworks" + library_name,
                        new_library_path])
        # update self-reference of file just copied
        subprocess.run(["install_name_tool", "-change", src,
                        "@executable_path/../Frameworks/" + library_name,
                        new_library_path])


def main():
    checker = AppBundleChecker()
    checker.check()


if __name__ == "__main__":
    main()
