# Based on http://www.scons.org/wiki/ColorBuildMessages
# From David Sawyer

import sys

colors = {}
colors["cyan"] = "\033[96m"
colors["purple"] = "\033[95m"
colors["blue"] = "\033[94m"
colors["green"] = "\033[92m"
colors["yellow"] = "\033[93m"
colors["red"] = "\033[91m"
colors["end"] = "\033[0m"


# If the output is not a terminal, remove the colors
if not sys.stdout.isatty():
    for key, value in colors.items():
        colors[key] = ""

compile_source_message = "%sCompiling %s==> %s$SOURCE%s" % (
    colors["blue"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

compile_shared_source_message = "%sCompiling shared %s==> %s$SOURCE%s" % (
    colors["blue"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

link_program_message = "%sLinking Program %s==> %s$TARGET%s" % (
    colors["red"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

link_library_message = "%sLinking Static Library %s==> %s$TARGET%s" % (
    colors["red"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

ranlib_library_message = "%sRanlib Library %s==> %s$TARGET%s" % (
    colors["red"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

link_shared_library_message = "%sLinking Shared Library %s==> %s$TARGET%s" % (
    colors["red"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

java_library_message = "%sCreating Java Archive %s==> %s$TARGET%s" % (
    colors["red"],
    colors["purple"],
    colors["yellow"],
    colors["end"],
)

rdict = {}
rdict.update(
    CXXCOM=compile_source_message,
    CCCOM=compile_source_message,
    SHCCCOM=compile_shared_source_message,
    SHCXXCOM=compile_shared_source_message,
    ARCOM=link_library_message,
    RANLIBCOM=ranlib_library_message,
    SHLINKCOM=link_shared_library_message,
    LINKCOM=link_program_message,
    JARCOM=java_library_message,
    JAVACCOM=compile_source_message,
)


def generate(env):
    for k, v in rdict.items():
        sname = k + "STR"
        # Prepend the color text to the command string variable, if
        # present.  Otherwise use the color text as is.
        if k in env:
            env[sname] = v + "\n" + env[k]
        else:
            env[sname] = v


def exists(env):
    return True
