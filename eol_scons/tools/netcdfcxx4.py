
def generate(env):
    """
    Tool for the netcdf-cxx4 library which replaces the legacy C++ API.
    """
    env.Append(LIBS=['netcdf_c++4'])
    env.Require('netcdf')


def exists(env):
    return True
