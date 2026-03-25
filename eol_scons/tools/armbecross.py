# Copyright (c) 2007-present, NSF NCAR, UCAR
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
"""
scons arm tool

Customize an environment to use the GCC ARM cross-compiler tools.
"""

import eol_scons.utils


def generate(env, **kw):
    """
    Add construction variables for C compilers to an Environment.
    """

    env.Replace(AR="armbe-linux-ar")
    env.Replace(AS="armbe-linux-as")
    env.Replace(CC="armbe-linux-gcc")
    env.Replace(LD="armbe-linux-ld")
    env.Replace(CXX="armbe-linux-g++")
    env.Replace(LINK="armbe-linux-g++")
    env.Replace(RANLIB="armbe-linux-ranlib")
    env.Replace(LEX="armbe-linux-flex")
    env.Replace(
        KMAKE='make KERNELDIR=$KERNELDIR KCFLAGS="$KCFLAGS" ARCH=arm CROSS_COMPILE=armbe-linux-'
    )

    # Append /opt/arcom/bin to env['ENV']['PATH'],
    # so that it is the fallback if armbe-linux-gcc is
    # not otherwise found in the path.
    # But scons is too smart. If you append /opt/arcom/bin
    # to env['ENV']['PATH'], scons will remove any earlier
    # occurances of /opt/arcom/bin in the PATH, and you may
    # get your second choice for armbe-linux-gcc.
    # So, we only append /opt/arcom/bin if "which armbe-linux-gcc"
    # fails.

    if not exists(env):
        env.AppendENVPath("PATH", "/opt/arcom/bin")
        if not exists(env):
            print(
                "*** armbe-linux-gcc, armbe-linux-g++ not found on path: %s"
                % env["ENV"]["PATH"]
            )
            return

    print(
        "armbecross: found %s and %s"
        % (env.WhereIs("armbe-linux-gcc"), env.WhereIs("armbe-linux-g++"))
    )

    cxxrev = eol_scons.utils.get_cxxversion(env)
    if cxxrev is not None:
        env.Replace(CXXVERSION=cxxrev)


def exists(env):
    return bool(env.Detect("armbe-linux-gcc")) and bool(
        env.Detect("armbe-linux-g++")
    )
