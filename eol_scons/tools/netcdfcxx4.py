
def generate(env):
    """
    Tool for the netcdf-cxx4 library which replaces the legacy C++ API.
    """
    # env.AppendUnique(DEPLOY_SHARED_LIBS=['netcdf_cxx4'])
    env.AppendUnique(LIBS=['netcdf_c++4'])
    env.Require('netcdf')

def exists(env):
    return True
