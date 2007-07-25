import os
import SCons

import SCons.Scanner.IDL
idl_scanner = SCons.Scanner.IDL.IDLScan()

omniidl_builder = SCons.Builder.Builder(action='$OMNIIDL_COM',
                                        source_scanner = idl_scanner)

def generate(env):
    """Add builders and construction variables for omniidl."""
    omniorb_top="/net/opt_lnx/local_fc2/omniORB"
    env['OMNIORB_TOP'] = omniorb_top
    env['BUILDERS']['OmniIDL'] = omniidl_builder
    env['OMNIIDL'] = os.path.join("$OMNIORB_TOP","bin","omniidl")
    env['OMNIIDL_OUTPUTDIR'] = '$TARGET.dir/..'
    env['OMNIIDL_FLAGS'] = '-bpython -C$OMNIIDL_OUTPUTDIR'
    env['OMNIIDL_COM'] = '$OMNIIDL $OMNIIDL_FLAGS $SOURCE'


def exists(env):
    return True

