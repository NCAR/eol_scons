
def generate(env):
    """
    Tool for the legacy netcdf-c++ library.
    """
    # env.AppendUnique(DEPLOY_SHARED_LIBS=['netcdf_cxx'])
    env.AppendUnique(LIBS=['netcdf_c++'])
    env.Require('netcdf')

def exists(env):
    return True
