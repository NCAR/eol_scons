
# This tool attaches an object to the environment which serves as a proxy
# for a postgres test database running in the background.
# To run tests against a live postgresql database, we want an abstraction
# to control the database before, during, and after running test commands.
#
# Create the object and setup all of the parameters.  Provide
# "personalities" to impersonate different kinds of databases such as
# aircraft on-board, aircraft ground, soundings, and so on.
#
# pg = env.PostgresTestDB()

# Return the environment variables necessary to connect to the
# test database:
#
# pg.getEnvironment()

# These are all synchronous, but they control an asynchronous 
# child process.
#
# pg.start()
# pg.stop()

# pg.startRealtime()
# pg.stopRealtime()
# pg.load(sqlfile)


import zlib
import os
import subprocess as sp
import shutil
import re

from SCons.Script import BUILD_TARGETS

_postgresql_conf = """
# An empty list is supposed to disable network listening.
listen_addresses = ''
# Use the data directory for unix sockets.
%(socketparam)s = '%(PGHOST)s'
"""


class PostgresTestDB(object):

    def __init__(self, cwd=None):

        # Save off the directory from which commands should operate, in
        # case there are different test databases for different directories
        # within the same source tree.
        self.cwd = cwd
        if not self.cwd:
            self.cwd = os.getcwd()
        # We want the port to depend on the current directory, so it is
        # consistent between runs without colliding with other instances
        # running from other working directories.
        port = "5%s00000" % (abs(zlib.crc32(self.cwd)))
        self.PGPORT = port[0:5]
        self.PGHOST = "/tmp"
        #
        # The pgdata directory is also put in /tmp, because sometimes CI
        # servers (ie, hudson and jenkins) do not have the right
        # permissions for initdb to create the pgdata directory inside the
        # source tree.
        #
        self.PGDATA = "/tmp/pgdata.%s" % (self.PGPORT)
        self.pgversion = None

    def getVersion(self):
        if not self.pgversion:
            p = sp.Popen(['initdb', '--version'], stdout=sp.PIPE, shell=False)
            self.pgversion = p.communicate()[0].split()[2]
        return self.pgversion

    def init(self):
        "Create the PGDATA directory and setup the configuration."
        self.stop()
        shutil.rmtree(self.PGDATA, ignore_errors=True)
        print("Postgres version: %s" % (self.getVersion()))
        self.initdb()
        socketparam = "unix_socket_directories"
        if self.getVersion().startswith("8."):
            socketparam = "unix_socket_directory"
        cfile = "%s/postgresql.conf" % (self.PGDATA)
        ctext = _postgresql_conf % { "PGHOST":self.PGHOST,
                                     "socketparam":socketparam }
        with open(cfile, "w") as cf:
            cf.write(ctext)

    def _popen(self, cmd, env=None, **args):
        print("Running: %s" % " ".join(cmd))
        if not env:
            env = self.getEnvironment()
        return sp.Popen(cmd, shell=False, env=env, **args)

    def start(self):
        p = self._popen(["pg_ctl", "-w", "-o", "-i", "start"])
        p.wait()

    def stop(self):
        p = self._popen(["pg_ctl", "-m", "fast", "-w", "stop"])
        p.wait()

    def initdb(self):
        p = self._popen(["initdb"])
        p.wait()

    def psql(self, database, command):
        p = self._popen(["psql", database, "-c", command])
        p.wait()

    def dump(self, host, user, db, path):
        "Write SQL dump of @p user, @p host, @p db to @p path."
	cmd = ["pg_dump", "-i", "-C", "--no-owner", "-v", "-h",
               host, "-U", user, "--format=p", "-f", path, db]
        p = self._popen(cmd, env=os.environ)
        p.wait()

    def getEnvironment(self):
        env = os.environ.copy()
        env['PGPORT'] = self.PGPORT
        env['PGHOST'] = self.PGHOST
        env['PGDATA'] = self.PGDATA
        return env

    def setupAircraftDatabase(self, sqlfile):
        self.start()
        self.psql("template1", "create user ads with createdb createuser;")
        with open(sqlfile) as sf:
            p = self._popen(["psql", "template1"], stdin=sf)
            p.communicate()
        # gunzip -c $SQLGZ | psql template1
	# pg_restore -i -C -d postgres real-time.sqlz

    def action_run_aircraftdb(target, source, env):
        pg = env.PostgresTestDB()
        pg.init()
        pg.start()
        # Find the source that is the SQL dump.
        sql = [ s for s in source if str(s).endswith('.sql') ]
        if not sql:
            raise SCons.Errors.StopError, "No SQL source."
        sql = sql[0]
        pg.setupAircraftDatabase(sql.get_abspath())
        # Also set PGDATABASE to the name of the database just created, so
        # programs can connect to the database without knowing the name.
        matches = re.search(r'CREATE DATABASE "([^"]+)"', sql.get_contents())
        if matches:
            env['ENV']['PGDATABASE'] = matches.group(1)
        return 0

    action_run_aircraftdb = staticmethod(action_run_aircraftdb)

    def action_stopdb(target, source, env):
        pg = env.PostgresTestDB()
        pg.stop()
        return 0

    action_stopdb = staticmethod(action_stopdb)

def dumpdb(target, source, env):
    platform = env['AIRCRAFT']
    db = "real-time"
    if platform:
        db = db + "-" + platform
    pg = env.PostgresTestDB()
    pg.dump("eol-rt-data.fl-ext.ucar.edu", "ads", db, target[0].get_abspath())


def DumpAircraftSQL(env, sqltarget, aircraft):
    if [ t for t in BUILD_TARGETS if str(t).endswith(sqltarget) ]:
        sql = env.Command(sqltarget, None, env.Action(dumpdb), 
                          AIRCRAFT=aircraft)
        env.AlwaysBuild(sql)


def _get_instance(env, cwd=None):
    # Only create one database test object per environment, so the same
    # object can be retrieved by separate calls to our PostgresTestDB()
    # environment method.
    pg = env.get('POSTGRES_TESTDB')
    if not pg:
        pg = PostgresTestDB(cwd)
        env['POSTGRES_TESTDB'] = pg
        # Also add the connection settings to the SCons ENV so they will
        # be set when running commands.
        env['ENV']['PGPORT'] = pg.PGPORT
        env['ENV']['PGHOST'] = pg.PGHOST
        env['ENV']['PGDATA'] = pg.PGDATA

    return pg


def generate(env):
    env.AddMethod(_get_instance, "PostgresTestDB")
    env.AddMethod(DumpAircraftSQL, "DumpAircraftSQL")

def exists(env):
    pgctl = env.WhereIs('pg_ctl')
    if not pgctl:
        SCons.Warnings.warn(
            SvnInfoWarning,
            "Could not find pg_ctl program.  "
            "postgres_testdb tool not available.")
        return False
    return True
