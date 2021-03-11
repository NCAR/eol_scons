
def generate(env):
    """
    Tool for the legacy netcdf-c++ library.
    """
    env.Append(LIBS=['netcdf_c++'])
    env.Require('netcdf')


def exists(env):
    return True
