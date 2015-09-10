
import os
def generate(env):
	dorade_top='/code/vanandel/rdss'
	ddu = os.path.join(dorade_top, 'spol','ddutils')
        env.Append(CPPPATH=[
	os.path.join(dorade_top, 'spol','include'), ddu ],
	LIBPATH=[ddu,], LIBS=['ddm',])
	




def exists(env):
    return True

