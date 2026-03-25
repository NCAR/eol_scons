# This tool file is discovered and loaded by eol_scons automatically when the
# vector library is added as a dependency.

from SCons.Script import Environment, Export

env = Environment(tools=['default'])

libvector = env.Library('vector', ['Vector.cc'])


def vector(env):
    # The Library() method adds the library node to the list of global
    # targets, which allows it to be looked up by name in other environments.
    # This tool function uses the AppendLibrary() method as a simple way to
    # add a global target by name to the LIBS list.  See
    # interpolate/SConscript for a different approach.
    env.AppendLibrary('vector')


Export('vector')
