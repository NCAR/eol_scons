import os, os.path
import eol_scons
from SCons.Options import PathOption

print "Adding SPOL_PREFIX to options."
eol_scons.GlobalOptions().AddOptions (
	PathOption('SPOL_PREFIX', 'Installation prefix for SPOL software.',
		   '/opt/spol'))

def generate(env):
	# Re-apply options in case this package has just now been required
	# by this environment, meaning this environment has not been updated
	# with the additional options.
	eol_scons.GlobalOptions().Update(env)
	SpolPrefix = env['SPOL_PREFIX']
	SpolBinDir = os.path.join(SpolPrefix, 'bin')
	SpolLibDir = os.path.join(SpolPrefix, 'lib')
	SpolPythonLibDir = os.path.join(SpolPrefix, 'lib', 'python')
# 	Export("SpolPrefix")
# 	Export("SpolBinDir")
# 	Export("SpolLibDir")
# 	Export("SpolPythonLibDir")
	env["SpolPrefix"] = SpolPrefix
	env["SpolBinDir"] = SpolBinDir
	env["SpolLibDir"] = SpolLibDir
	env["SpolPythonLibDir"] = SpolPythonLibDir
        env.Append(CPPPATH=['#spol/include',])


def exists(env):
    return True

