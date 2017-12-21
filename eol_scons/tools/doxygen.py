# -*- python -*-

from __future__ import print_function
import os
import hashlib
import string
import SCons
import SCons.Node
import SCons.Util
from SCons.Script import Builder
from SCons.Script import Action
from SCons.Node import FS
import shutil
import fnmatch
from fnmatch import fnmatch

try:
    from StringIO import StringIO
except:
    from io import StringIO

_debug = False

def ddebug():
    return _debug

def dprint(msg):
    if ddebug():
        print(msg)

class DoxygenWarning(SCons.Warnings.Warning):
    pass

def apidocssubdir(node):
    """
    Return the nominal subdirectory path for this node within the source
    tree, to be used as a unique name and path under the top apidocs
    destination directory.
    """
    if node.srcnode() != node:
        dprint("apidocssubdir(%s): translating to source node '%s'" %
               (node.abspath, str(node.srcnode())))
        node = node.srcnode()
    if not node.isdir():
        dprint("apidocssubdir(%s): converting non-dir to dir '%s'" %
               (node.abspath, str(node.get_dir())))
        node = node.get_dir()
    top = node.Dir('#')
    dprint('top=%s' % str(top))
    if node == top:
        subdir = 'root'
    else:
        subdir = str(node.get_path(top))
    subdir = subdir.replace(os.sep, '_')
    dprint("apidocssubdir(%s) ==> %s" % (node.abspath, subdir))
    return subdir


def tagfilename(node):
    """
    Construct the name of the tag file for the source directory
    in the given node.
    """
    subdir = apidocssubdir(node)
    qtag = subdir + '.tag'
    dprint("tagfilename(%s) ==> %s" % (str(node), qtag))
    return qtag


def apidocsdir(env):
    subdir = apidocssubdir(env.Dir('.'))
    docsdir = os.path.join(env['APIDOCSDIR'], subdir)
    dprint("apidocsdir(%s) ==> %s" % (env.Dir('.').abspath, str(docsdir)))
    return docsdir


def CheckMissingHeaders(subdir, doxfiles, ignores):

    found = []
    # print "Subdir: ", subdir
    # print "Files: ", doxfiles
    # print "Ignores: ", ignores
    for root, dirs, files in os.walk(subdir):
        files = filter(lambda f: 
                       not fnmatch(f, "moc_*")
                       and not fnmatch(f, "ui_*")
                       and not fnmatch(f, "*.ui*")
                       and not fnmatch(f, "uic_*")
                       and fnmatch(f, "*.h"), files)
        found += [os.path.normpath(os.path.join(root, f)) for f in files]
        if '.svn' in dirs:
            dirs.remove('.svn')

    known = [ os.path.normpath(os.path.join(subdir, p))
              for p in doxfiles+ignores ]
    missing = [ f for f in found if f not in known ]
    missing.sort()
    if len(missing) > 0:
        print("Header files missing in "+subdir+":")
        print("  "+"\n  ".join(missing))
    return missing


def Doxyfile_Emitter (target, source, env):
    """
    Modify the source list to create the correct dependencies.  Due to an
    error on Gary's part which established a poorly-thought-out convention,
    the source nodes are used to generate the INPUT setting in the
    Doxyfile, even though they are not actual dependencies for the Doxyfile
    itself, since the Doxyfile does not need to be regenerated just because
    a source file changes.  Therefore the source for the Doxyfile becomes a
    Value node containing the Doxyfile contents for all the current
    environment settings, and the only other possible dependency is another
    Doxyfile whose contents are included in the generated Doxyfile.

    So the Doxyfile should be regenerated only if the Value node contents
    change, meaning environment settings or the source list have changed.
    However, there are cases (such as in the Aeros source tree) where the
    Doxyfile is always regenerated, apparently because SCons thinks the
    Value node depenency changed even though it didn't.  The reason is
    still a mystery, and the solution evades me.
    """
    dprint("entering doxyfile_emitter(%s,%s):" %
           (",".join([str(t) for t in target]),
            ",".join([str(s) for s in source])))
    contents = Doxyfile_contents(target, source, env)
    source = [ env.Value(contents) ]
    try:
        source.append(env.File(env['DOXYFILE_FILE']))
        dprint("added Doxyfile dependency: " + str(source[-1]))
    except KeyError:
        pass

    if ddebug():
        dprint("leaving doxyfile_emitter: targets=(%s), sources=(%s)" %
               (",".join([str(t) for t in target]),
                ",".join([hashlib.md5(str(s)).hexdigest() for s in source])))
    return target, source
    

def Doxyfile_Builder (target, source, env):
    "The source node should be the Doxyfile contents generated in the emitter."
    docsdir = str(target[0].get_dir())
    try:
        os.makedirs(docsdir)
    except:
        if not os.access(docsdir, os.W_OK):
            raise
    dprint(docsdir + " exists")
    doxyfile = target[0].get_abspath()
    if ddebug() and os.path.exists(doxyfile):
        doxyfilebak = doxyfile + '.bak'
        shutil.move(doxyfile, doxyfilebak)
        dprint("saved original Doxyfile as %s" % (doxyfilebak))
    dprint("writing doxyfile: %s" % (doxyfile))
    dfile = open(doxyfile, "w")
    dfile.write(source[-1].get_text_contents())
    dfile.close()


def Doxyfile_contents (target, source, env):
    """
    Generate a standard Doxyfile for the Doxygen builder.  This builder expects
    one target, the name of the doxygen config file to generate.  The
    generated config file sets directory parameters relative to the target
    directory, so it expects Doxygen to run in the same directory as the
    config file.  The documentation output will be written under that same
    directory.  The return value is the contents of the Doxyfile, suitable
    for insertion into a Value() node or for writing directly to the target
    Doxyfile.

    This generator uses these environment variables:

    DOXYFILE_FILE

    The name of a doxygen config file that will be used as the basis for
    the generated configuration.  This file is copied into the destination
    and then appended according to the DOXYFILE_TEXT and DOXYFILE_DICT
    settings.

    DOXYFILE_TEXT

    This should hold verbatim Doxyfile configuration text which will be
    appended to the generated Doxyfile, thus overriding any of the default
    configuration settings.
                        
    DOXYFILE_DICT

    A dictionary of Doxygen configuration parameters which will be
    translated to Doxyfile form and included in the Doxyfile, after the
    DOXYFILE_TEXT settings.  Parameters which specify files or directory
    paths should be given relative to the source directory, then this
    target adjusts them according to the target location of the generated
    Doxyfile.

    The order of precedence is DOXYFILE_DICT, DOXYFILE_TEXT, and
    DOXYFILE_FILE.  In other words, parameter settings in DOXYFILE_DICT and
    then DOXYFILE_TEXT override all others.  A few parameters will always
    be enforced by the builder over the DOXYFILE_FILE by appending them
    after the file, such as OUTPUT_DIRECTORY, GENERATE_TAGFILE, and
    TAGFILES.  This way the template Doxyfile generated by doxygen can
    still be used as a basis, but the builder can still control where the
    output gets placed.  If any of the builder settings really need to be
    overridden, such as to put output in unusual places, then those
    settings can be placed in DOXYFILE_TEXT or DOXYFILE_DICT.

    DOXYFILE_IGNORES

    If given, this is a list of header file names which have been
    excluded explicitly from doxygen input.  The builder will check for
    any header files which are not either in the builder source or in
    the list of ignores.  Those header files will be reported as missing
    and the build will fail.

    Here are examples of some of the Doxyfile configuration parameters
    which typically need to be set for each documentation target.  Unless
    set explicitly, they are given defaults in the Doxyfile.
    
    PROJECT_NAME        Title of project, defaults to the source directory.
    PROJECT_NUMBER      Version string for the project.  Defaults to 1.0

    """ 

    dprint("entering doxyfile_contents...")
    topdir = target[0].Dir('#')
    subdir = source[0].get_dir()
    docsdir = str(target[0].get_dir())

    if 'DOXYFILE_IGNORES' in env:
        ignores = env['DOXYFILE_IGNORES']
        if CheckMissingHeaders(subdir.get_path(env.Dir('#')),
                               [s.get_path(subdir) for s in source], 
                               ignores):
            return -1

    doxyfile = None
    try:
        doxyfile = env.File (env['DOXYFILE_FILE'], subdir)
    except KeyError:
        pass

    dfile = StringIO()
    # These are defaults that any of the customization methods can
    # override.  Latex is off because it is rarely used, better to enable
    # it specifically for the projects which use it.
    dfile.write("""
SOURCE_BROWSER         = YES
INPUT                  = .
GENERATE_HTML          = YES
GENERATE_LATEX         = NO
PAPER_TYPE             = letter
PDF_HYPERLINKS         = YES
USE_PDFLATEX           = YES
GENERATE_RTF           = NO
GENERATE_MAN           = NO

# Allow source code to ifdef out sections which cause warnings from
# doxygen, like explicit template instantiations and recursive class
# templates.
PREDEFINED = DOXYGEN

# 
# Specifically disable extracting private class members and file static
# members, for the case of generating documentation for only the public
# interface of a library.  Instead require individual directories to
# override those as needed.
#
EXTRACT_ALL	       = YES
EXTRACT_STATIC	       = NO
EXTRACT_PRIVATE	       = NO

CLASS_GRAPH            = YES
COLLABORATION_GRAPH    = YES
INCLUDE_GRAPH          = YES
INCLUDED_BY_GRAPH      = YES
GRAPHICAL_HIERARCHY    = YES
REFERENCED_BY_RELATION = NO
REFERENCES_RELATION = NO

# Allow files without extensions and .dox files to be parsed like source
# files, for projects which include README files and the like as part of
# the doxygen source.  Files with non-standard extensions worked implicitly
# in older doxygen versions, but apparently newer versions need an explicit
# mapping.

EXTENSION_MAPPING = no_extension=C++ dox=C++

""")

    dot_path = env.WhereIs("dot")
    if dot_path:
        dfile.write("DOT_PATH = %s\n" % os.path.dirname(dot_path))

    # These are defaults which can be overridden by the DOXYFILE_TEXT
    # or DOXYFILE_DICT sections below.
    #
    dfile.write("PROJECT_NAME           = %s\n" % subdir)
    dfile.write("PROJECT_NUMBER         = \"Version 0.1\"\n")

    # Further customizations which can override the settings above.
    if doxyfile:
        ifile = open(doxyfile.path)
        dfile.write(ifile.read())
        ifile.close()

    # The rest are not defaults.  They are required for things to be put
    # into the right places, thus they are last.
    #
    dfile.write("INPUT                  = \\\n")
    for s in source:
        # Source files named Doxyfile or index.html are not inputs.
        if ((not doxyfile or s.path != doxyfile.path) and 
            (s.name != 'index.html')):
            dfile.write("%s \\\n" % s.get_abspath())
            
    dfile.write ("\n")
    outputdir = docsdir
    dfile.write("OUTPUT_DIRECTORY       = %s\n" % outputdir)
    dfile.write("HTML_OUTPUT            = html\n")
    dfile.write("LATEX_OUTPUT           = latex\n")
    dfile.write("RTF_OUTPUT             = rtf\n")
    dfile.write("MAN_OUTPUT             = man\n")
    dfile.write("GENERATE_TAGFILE       = %s\n" % \
                os.path.join(outputdir, tagfilename(source[0])))

    # Parse DOXREF for references to other tag files, internal and
    # external.  Each name in the tag reference refers to the full path of
    # the part of the source tree it comes from.  That way all tag files
    # and subdirectories under the documentation directory will be unique.
    # The names are flattened by replacing slashes with underscoers, so the
    # path for references between local documentation will always be
    # obvious, just '../<tagname>/html'.

    # If the tagfile already exists and has a reference (docpath), then use
    # it as is.  Since doxytag was declared obsolete in release 1.8, it is
    # no longer possible to generate the tag file directly, so the only way
    # to link to external docs is to reference an existing tag file and
    # existing html documentation.  If the tagfile does not have a docpath,
    # then we assume the tagfile and the apidocs are generated from this
    # source, so we generate the implicit docpath for that tagfile.  If the
    # tagfile has an explicit reference but the tagfile itself does not
    # already exist, then there's no point in including it in the tagfile
    # list.

    doxref = env['DOXREF']
    dprint("Parsing DOXREF for tag references: %s" % (str(doxref)))
    tagfiles={}
    for tagref in doxref:
        tag = env.subst(tagref)
        (tagpath, colon, docpath) = tag.partition(':')
        if not tagpath:
            print("Ignoring empty doxref: %s" % (tagref))
        elif docpath:
            # docpath is explicit, use it as is.
            if os.path.exists(tagpath):
                tagfiles[tag] = "%s=%s" % (tagpath, docpath)
                dprint("Using explicit doxref: %s" % (tagfiles[tag]))
            else:
                print("Tagfile with explicit doxref does not exist, ignored: %s" %
                      (tag))
        else:
            # Assume the tagfile will be generated under apidocs
            qtag=tagpath.replace("/","_")
            tagdir="%s/../%s" % (outputdir, qtag)
            tagpath="%s/%s.tag" % (tagdir, qtag)
            docpath="../../%s/html" % (qtag)
            tagfiles[tag] = "%s=%s" % (tagpath, docpath)
            dprint("Expanded tagfile reference: %s" % (tagfiles[tag]))

    if len(tagfiles) > 0:
        dfile.write("TAGFILES = %s\n" % (" ".join(tagfiles.values())))

    # The last of the customizations.  They have to go here for the case
    # of generating output in unusual locations, where it's up to the
    # caller of the builder to set the target correctly.
    #
    dfile.write(env.subst(env['DOXYFILE_TEXT']))

    for k, v in env['DOXYFILE_DICT'].items():
        dfile.write ("%s = \"%s\"\n" % (k, env.subst(str(v))))

    dprint("leaving doxyfile_contents.")
    doxyfile = dfile.getvalue()
    dfile.close()
    return doxyfile


def doxyfile_message (target, source, env):
    return "creating Doxygen config file '%s'" % target[0]

doxyfile_variables = [
    'DOXYFILE_TEXT',
    'DOXYFILE_DICT',
    'DOXYFILE_FILE',
    'DOXREF'
    ]

doxyfile_action = Action( Doxyfile_Builder, doxyfile_message,
                          varlist = doxyfile_variables)

doxyfile_builder = Builder( action = doxyfile_action,
                            emitter = Doxyfile_Emitter )


def _parse_doxyfile(dfilenode):
    "Parse a Doxyfile into a dictionary."
    parms = {}
    dprint("parsing doxyfile...")

    contents = dfilenode.get_text_contents()
    dfile = StringIO(contents)
    lines = dfile.readlines()
    dfile.close()
    current = ""
    for line in lines:
        line = line.rstrip()
        if line.endswith('\\'):
            current = current + line[:-1] + ' '
            continue
        else:
            current = current + line
        current = current.strip()
        if not current.startswith('#'):
            (lpart, equals, rpart) = current.partition('=')
            lpart = lpart.strip()
            rpart = rpart.strip()
            if lpart and rpart:
                parms[lpart] = rpart
                dprint("%s=%s" % (lpart, rpart))
        current = ""
    return parms


def Doxygen_Emitter (target, source, env):
    """
    Add the output HTML index file as the doxygen target, representative of
    all of the files which will be generated by doxygen.  The first (and
    only) source should be the Doxyfile, and the output is expected to go
    under that directory.
    
    If an explicit target location has been specified (as in it hasn't
    defaulted to be the same as the source), then use that target.
    """
    dprint("entering Doxygen_Emitter")

    # There are two source scenarios for the doxygen builder.  The source
    # is a permanent, manually-edited Doxyfile which always exists, or the
    # source is a Doxyfile target generated by the Doxyfile builder, in
    # which case it may not exist yet.  If the former, then the file can be
    # parsed directly for extra dependency and target information like the
    # input files and output directory.  If the latter, then we need to
    # find the Value() node emitted by the Doxyfile builder which contains
    # the contents of the Doxyfile.  We need to setup the dependencies
    # correctly the first time, even when the Doxyfile has not been written
    # yet, otherwise SCons rebuilds the doxygen target unnecessarily just
    # because the dependencies get added after the Doxyfile exists.

    children = source[0].children(scan=0)
    dfilenode = None
    for cnode in children:
        if isinstance(cnode, SCons.Node.Python.Value):
            dfilenode = cnode
            break
    if dfilenode:
        dprint("doxyfile contents found in Value node")
    else:
        dfilenode = source[0]
        dprint("doxyfile contents found in %s" % (dfilenode.get_abspath()))
    dfile = _parse_doxyfile(dfilenode)

    # The source file dependencies are in the INPUT parameter in the
    # Doxyfile.  Note that if the Doxyfile does not exist yet, then the
    # parser returns an empty dictionary and no inputs will be added as
    # depenndencies.  That's ok, assuming the doxygen builder will run
    # anyway since the Doxyfile will be created new.
    #
    # This might be done more properly with a source scanner registered
    # with the doxygen builder...
    #
    inputs = dfile.get('INPUT', "")
    dprint("%s: INPUT=%s" % (source[0].get_abspath(), inputs))
    inputs = inputs.split()
    for ip in inputs:
        if os.path.isdir(ip):
            source.append(env.Dir(ip))
        else:
            source.append(env.File(ip))

    # Tagfiles are also dependencies, and they are especially important
    # because inter-project links will not work if the subproject's tag
    # file is not generated before the project.

    tagspecs = dfile.get('TAGFILES', "").split()
    for spec in tagspecs:
        # A tag file is a dependency no matter what.  Either it is being
        # generated from this source tree, or it must already exist.
        (tagfile, equals, locn) = spec.partition('=')
        tagnode = env.File(tagfile)
        dprint("found tagfile specifier: %s, adding tagfile source: %s" %
               (spec, str(tagnode)))
        source.append(tagnode)

    output = dfile.get('OUTPUT_DIRECTORY', "")
    env['DOXYGEN_OUTPUT_DIRECTORY'] = output
    html = os.path.join(output, dfile.get('HTML_OUTPUT', 'html'))
    env['DOXYGEN_HTML_OUTPUT'] = html
    dprint("DOXYGEN_OUTPUT_DIRECTORY set: %s" % 
           (env.get('DOXYGEN_OUTPUT_DIRECTORY', "")))

    # Now that we know the output directory, we can set a target (assuming
    # html output) unless an explicit target was provided.
    t = target
    if str(target[0]) == str(source[0]):
        t = [ env.File(os.path.join(html, "index.html")) ]
        dprint("doxygen_emitter: target set to %s" % (str(t[0])))

    # This builder may also generate a tag file.
    tagfile = dfile.get('GENERATE_TAGFILE')
    if tagfile:
        t.append(env.File(tagfile))

    dprint("leaving Doxygen_Emitter")
    return t, source
    

doxygen_action = Action (['$DOXYGEN_COM'])

doxygen_builder = Builder( action = doxygen_action,
                           emitter = Doxygen_Emitter )

def Doxygen(env, target=None, source=None, **kw):
    "The Doxygen method is a pseudo-builder so it can add to Clean targets."
    if not source:
        source = target
    if not target:
        target = source
    tdoxygen = env.DoxygenBuilder(target, source, **kw)
    # The builder emitter should set the outputs we want to add to a 
    # Clean target.
    output = env.get('DOXYGEN_OUTPUT_DIRECTORY', None)
    dprint("output=%s" % (output))
    if output:
        dprint("adding Clean() for %s" % (output))
        env.Clean(tdoxygen, env.Dir(output))
    return tdoxygen


# Accumulate all the SOURCES and keywords passed into all Apidocs() builds
# into a single shared dictionary, so that all the sources in a source tree
# can be added to one Doxyfile.

_project = {}

_disable_subprojects = False

def ApidocsDisable(env, disable):
    global _disable_subprojects
    _disable_subprojects = disable

def _projectAddApidocs(env, source, **kw):
    global _project
    _project.update(kw)
    sources = _project.get("SOURCE", [])
    sources.extend([env.File(s) for s in source])
    _project["SOURCE"] = sources
    return _project


def Apidocs(env, source, **kw):
    "Pseudo-builder to generate documentation under apidocs directory."
    _projectAddApidocs(env, source, **kw)
    if _disable_subprojects:
        return env.Dir('#/apidocs')
    target = os.path.join(apidocsdir(env), 'Doxyfile')
    doxyfile = env.Doxyfile(target=target, source=source, **kw)
    # This just keeps scons from removing the target before the builder
    # writes it, so the builder can save a backup of the original for
    # diagnostics.
    env.Precious(doxyfile)
    tdoxygen = env.Doxygen(source=doxyfile, **kw)
    return tdoxygen


def ApidocsProject(env, name, version, source=None, **kw):
    """
    Pseudo-builder to generate documentation from all the source files
    accumulated by the global project dictionary.  The name and version are
    required to override any settings made by the subprojects.  Additional
    source files can be passed via @p source.
    """
    doxdict = kw.get('DOXYFILE_DICT', {})
    doxdict.update({'PROJECT_NAME':name, 'PROJECT_NUMBER':version})
    kw['DOXYFILE_DICT'] = doxdict
    project = _projectAddApidocs(env, source or [], **kw)
    docsdir = os.path.join(env['APIDOCSDIR'], name)
    target = os.path.join(docsdir, 'Doxyfile')
    kw = {}
    kw.update(project)
    del kw['SOURCE']
    doxyfile = env.Doxyfile(target=target, source=project['SOURCE'], **kw)
    env.Precious(doxyfile)
    tdoxygen = env.Doxygen(source=doxyfile, **kw)
    return tdoxygen
    

def ApidocsIndex (env, source, **kw):
    doxyconf = """
OUTPUT_DIRECTORY       = apidocs
HTML_OUTPUT            = .
RECURSIVE              = NO
SOURCE_BROWSER         = NO
ALPHABETICAL_INDEX     = NO
GENERATE_LATEX         = NO
GENERATE_RTF           = NO
GENERATE_MAN           = NO
GENERATE_XML           = NO
GENERATE_AUTOGEN_DEF   = NO
ENABLE_PREPROCESSING   = NO
CLASS_DIAGRAMS         = NO
HAVE_DOT               = NO
GENERATE_HTML          = YES
"""
    kw['DOXYFILE_TEXT'] = doxyconf
    df = env.Doxyfile(target="%s/Doxyfile" % env['APIDOCSDIR'],
                      source=source, **kw)
    dx = env.Doxygen(target="%s/index.html" % env['APIDOCSDIR'],
                     source=[df], **kw)
    return dx

from SCons.Script import Environment

def SetDoxref(env, name, tagfile, url):
    """
    Generate the correct DOXREF syntax for the given tagfile and url, and
    assign that doxref to the construction variable given by name.  The
    variable name should match what the corresponding tool adds to DOXREF,
    usually by calling AppendDoxref().  See AppendDoxref() in the default
    eol_scons Environment.
    """
    env[name] = env.File(env.subst(tagfile)).get_abspath() + ":" + url


def generate(env):
    """Add builders and construction variables for DOXYGEN."""
    # print "doxygen.generate(%s)" % env.Dir('.').get_path(env.Dir("#"))
    env['BUILDERS']['Doxyfile'] = doxyfile_builder
    env['BUILDERS']['DoxygenBuilder'] = doxygen_builder
    env.SetDefault(DOXREF=[])
    env.SetDefault(DOXYFILE_TEXT="")
    env.SetDefault(DOXYFILE_DICT={})
    env.SetDefault(DOXYGEN='doxygen')
    env.SetDefault(DOXYGEN_FLAGS='')
    env.SetDefault(DOXYGEN_COM='$DOXYGEN $DOXYGEN_FLAGS $SOURCE')
    env.SetDefault(APIDOCSDIR='#apidocs')
    env.AddMethod(Apidocs, "Apidocs")
    env.AddMethod(ApidocsDisable, "ApidocsDisable")
    env.AddMethod(ApidocsProject, "ApidocsProject")
    env.AddMethod(Doxygen, "Doxygen")
    env.AddMethod(ApidocsIndex, "ApidocsIndex")
    env.AddMethod(SetDoxref, "SetDoxref")
    # Set the path to the eol_scons README file in the environment, so
    # doxygen targets can reference it in project documentation without
    # hardcoding the path to it.
    readme = os.path.join(os.path.dirname(__file__), "..", "README")
    readme = os.path.abspath(readme)
    env.SetDefault(EOL_SCONS_README=env.File(readme))

def exists(env):
    return env.Detect ('doxygen')
