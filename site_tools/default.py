
"""default

Override the built-in scons default tool and propagate the tool path,
so that we can extend the built-in tools even when they are not
specified explicitly in the tools list.
"""
import eol_scons

def generate(env):
    eol_scons._generate(env)

def exists(env):
    return 1
