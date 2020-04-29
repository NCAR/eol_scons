"""
Tool to access functionality in eol_scons.postgres.testdb.

See that module for documentation.
"""

import os

import eol_scons.postgres.testdb as pgt

def dumpdb(target, _source_, env):
    platform = env['AIRCRAFT']
    db = "real-time"
    if platform:
        db = db + "-" + platform
    pg = env.PostgresTestDB()
    pg.dump("eol-rt-data.eol.ucar.edu", "ads", db, target[0].get_abspath(),
            env=os.environ)


def DumpAircraftSQL(env, sqltarget, aircraft):
    from SCons.Script import BUILD_TARGETS
    if [t for t in BUILD_TARGETS if str(t).endswith(sqltarget)]:
        sql = env.Command(sqltarget, None, env.Action(dumpdb), 
                          AIRCRAFT=aircraft)
        env.AlwaysBuild(sql)


def _get_instance(env, cwd=None, personality="aircraft"):
    # Only create one database test object per environment, so the same
    # object can be retrieved by separate calls to our PostgresTestDB()
    # environment method.
    pg = env.get('POSTGRES_TESTDB')
    if not pg:
        if personality == "aircraft":
            pg = pgt.AircraftTestDB(cwd)
        else:
            pg = pgt.PostgresTestDB(cwd)
        env['POSTGRES_TESTDB'] = pg
        # Also add the connection settings to the SCons ENV so they will
        # be set when running commands.
        env['ENV'].update(pg.getEnvironment({}))
    return pg


def generate(env):
    env.AddMethod(_get_instance, "PostgresTestDB")
    env.AddMethod(DumpAircraftSQL, "DumpAircraftSQL")
    # Put the path to the module in the shell environment, so test scripts
    # can call it directly as a script.
    ptdb = pgt.getPath()
    env.SetDefault(POSTGRES_TESTDB_PATH=ptdb)
    env['ENV']['POSTGRES_TESTDB_PATH'] = env['POSTGRES_TESTDB_PATH']


def exists(env):
    pgctl = env.WhereIs('pg_ctl')
    if not pgctl:
        import SCons
        SCons.Warnings.warn(
            SCons.Warnings.Warning,
            "Could not find pg_ctl program.  "
            "postgres_testdb tool not available.")
        return False
    return True
