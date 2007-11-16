#
# Tool for OpenDDS.  This will set up appropriate paths to find OpenDDS headers 
# and libraries, but will not add any DDS libraries to the link, since it is
# not known which of the DDS libraries are desired.
#
import os
import string
import re
from eol_scons.chdir import ChdirActions
from SCons.Options import PathOption

options = None
mykey = "HAS_PKG_OPENDDS"

def generate(env):

  global options
  if not options:
    options = env.GlobalOptions()
    dds_root = env.FindPackagePath('DDS_ROOT', '$OPT_PREFIX/OpenDDS*')
    options.AddOptions(PathOption('DDS_ROOT', 'DDS_ROOT directory.', dds_root))
  options.Update(env)
  
  # Use the existence of a key in the env to separate the DDS tool into
  # what need only be applied once and what must be applied every time this
  # tool is Require()d by another package.  Basically that means the library
  # must always be appended; everything else happens once.

  if not env.has_key(mykey):
    env.Require(['tao', 'ace', 'doxygen'])
    
    dds_root = env['DDS_ROOT']
    env['ENV']['DDS_ROOT'] = dds_root
    
    env.AppendUnique(CPPPATH=[dds_root])
    
    libpath=os.path.join(dds_root, 'lib')
    env.Append(LIBPATH=[libpath, ])
    env.AppendUnique(RPATH=[libpath])

    env.AppendDoxref("dds:%s/html/dds" % (dds_root))
    env[mykey] = 1

  env.DdsLibrary = DdsLibrary


def exists(env):
    return True

# 
# A DDS project simply defines one or more
# datatypes that will be handled by DDS. This is
# done in an idl file. A raft of supporting
# code and idl is generated from the original
# idl definition of the datatype.
#
# example usage:
# import os
# import DDSLib
# env = Environment(ENV = os.environ)
# lib = DDSLib.DdsLibrary('EldoraDds.idl', env)
#
# -------------------------------------------
#
# Create a library containing all DDS routines
# required for both server and client
#
# @param idlFile The idl file defining the DDS for a particular type
# #param env 
def DdsLibrary(idlFile, env):
    # get our current absolute directory, needed
    # for some later comands which must be executed here.
    curDir = env.Dir('.').get_abspath()

    #
    # ------------------------------------------
    #
    # get a list of files produced by the tao_idl processing of
    # the main idl. There will be three sublists:
    #[[*.cpp], [*.h], [*.inl]]
    target1 = taoIdlFiles(idlFile)

    #
    # Now process the main idl file with tao_idl.
    env.Command(target1, idlFile, 
                env['TAO_IDL'] + ' -o $SOURCE.dir -Gdcps $SOURCE')
    #
    # ------------------------------------------
    #
    # get a list of the types defined in the main idlFile
    ddsTypes = ddsTypeScanner(idlFile, env)
    #
    # get a list of files produced by the dcps_ts processing of
    # the type support idl files. There will be three sublists:
    #[[*.cpp], [*.h], [*.idl]]  (Note the idl output)
    target2 = dcpsTsFiles(ddsTypes)

    #
    # Process the main idl file with dcps_ts.pl
    # Execute the dcp_tl.pl command in the current directory,
    # since dcps_ts.pl will only put its output in the current directory.
    cmd = os.path.join(env['DDS_ROOT'], 'bin', 'dcps_ts.pl')
    dcpsCmd = ChdirActions(env, [cmd + " $SOURCE.file"], curDir)
    env.Command(target2, idlFile, dcpsCmd)
    #
    # save the names of the generated type support idl files
    typeSupportIdlFiles= target2[2]
    #
    # ------------------------------------------
    #
    # Process the generated type support idl files with
    # tao_idl
    cmd = os.path.join(env['ACE_ROOT'], 'bin', 'tao_idl')
    tao_cmd = ChdirActions(env, [env['TAO_IDL'] + ' -I ' + env['DDS_ROOT'] +
                                 ' $SOURCE.file'], curDir)
    target4 = []
    headers = []
    for ddsType in ddsTypes:
        typeSupportSource = ddsType+'TypeSupport.idl'
        target3 = taoIdlFiles(typeSupportSource)
        # while we are at it, save the generated .cpp and .h files
        target4.append(target3[0])
        headers.append(target3[1])
        # Send each type support idl file through tao_idl
        env.Command(target3, typeSupportSource, tao_cmd)
    #
    # ------------------------------------------
    #
    # Collect all of the source files, which will be compiled for the
    # library
    sources = target1[0] + target2[0] + target4
    headers.append(target1[1] + target2[1])
    
    # library name is the same as the IDL file base name, with the
    # .idl extension removed
    libName = os.path.splitext(os.path.basename(idlFile))[0]

    # Return the library itself, and also a list of source and header files
    # used to generate it (for documentation purposes)
    return [env.Library(libName, sources), sources, headers]

# -------- DDS support functions -----------
#
# Two functions are provided here which generate all of the file names
# associated with a a DDS project. These are taoIdlFiles() and
# dcpsTsFiles(). These functions create all of the filenames that will be
# created by the tao_idl and the dcps_ts.pl processors.
#
# These functions are used by the DsdLibrary() function.
#
# -------------------------------------------
#
# Create the filenames that are produced when tao_idl, with the -Gdcps
# option, processes an idl file
#
# @param idlFile The name of the idl file
# @return A 3 element list. The first slice contains a list of .cpp
# files. The second slice contains a list of .h files. The third slice
# contains a list of .inl files.
def taoIdlFiles(idlFile):
    root = idlFile.split('.')[0]
    cppFiles = [root+'C.cpp', root+'S.cpp']
    hFiles   = [root+'C.h', root+'S.h']
    inlFiles = [root+'C.inl', root+'S.inl']
    return [cppFiles, hFiles, inlFiles]

# Create the type support filenames that are produced for a given DDS data
# type definition within a DDS idl file.
def dcpsTsFiles(ddsTypes):
    cppFiles = []
    hFiles = []
    idlFiles = []
    for ddsType in ddsTypes:
        root = ddsType + 'TypeSupport'
        cppFiles.append(root+'Impl.cpp')
        hFiles.append(root+'Impl.h')
        idlFiles.append(root+'.idl')
    return [cppFiles, hFiles, idlFiles]

# -------------------------------------------
#
#
# Pick out the DDS types defined by the
# #pragma DCPS_DATA_TYPE 
# statements in the idl file. 
#
# Currently only returns the first type defined.  Need to fix the regular
# expression to process all lines.
#
# @param idlFile The idl file name
# @returns A tuple containing the type names. The type
# names do not include the module namespace qualification
#
def ddsTypeScanner(fileName, env):
# I don't know why this regular expression works to find the type name; I
# was on an airplane when writing it and didn't have access to the docs for
# regular expressions. It returns a tuple containing the modules name and
# the type name.  We just return the unqualified type names, i.e. the
# second slice of the tuple.
    dcps_re = re.compile(r'#pragma\s+DCPS_DATA_TYPE\s+"(\S+)::(\S+)*"', re.M)
    node = env.FindFile(fileName, '.')
    contents = node.get_contents()
    dcps_types = dcps_re.findall(contents)
    retVal = []
    for x in dcps_types:
        retVal.append(x[1])
    return retVal
