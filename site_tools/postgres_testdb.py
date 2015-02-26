"""Provide simple setup for an isolated test PostgreSQL database.

This tool attaches an object to the environment which serves as a proxy for
a postgres test database running in the background.  To run tests against a
live postgresql database, we want an abstraction to control the database
before, during, and after running test commands.

Create the object and setup all of the parameters.  Provide "personalities"
to impersonate different kinds of databases such as aircraft on-board,
aircraft ground, soundings, and so on.

   pg = env.PostgresTestDB()

Return the environment variables necessary to connect to the
test database:

   pg.getEnvironment()

This initializes the database, setting up the data directory and tweaking
the postgresql.conf file to allow local connections.

   pg.initdb()

These are all synchronous, but they control an asynchronous child process.

   pg.start()
   pg.stop()

This python module can also run as a main script.  It parses the command
line to run methods on the PostgresTestDB instance corresponding to the
current working directory.

"""


import zlib
import os
import subprocess as sp
import shutil
import re
import json

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
        self.settingsfile = self.PGDATA + "/postgres_testdb.json"
        self.pgversion = None
        self.PGUSER = None
        self.PGDATABASE = None

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

    def saveSetup(self):
        "Save the settings to a file for use later."
        with open(self.settingsfile, "w") as sfile:
            json.dump(self.getEnvironment({}), sfile)
            sfile.write("\n")

    def loadSetup(self):
        "Restore settings from the settings file."
        if os.path.exists(self.settingsfile):
            with open(self.settingsfile) as sfile:
                self.__dict__.update(json.load(sfile))

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

    def dump(self, host=None, user=None, db=None, path=None, args=None):
        "Write SQL dump of @p user, @p host, @p db to @p path."
        if not db:
            db = self.PGDATABASE
        if not path and db:
            path = db + ".sql"
	cmd = ["pg_dump", "-i", "-C", "--no-owner", "-v", "--format=p"]
        if args:
            cmd += args
        if host:
            cmd += ["-h", host]
        if user:
            cmd += ["-U", user]
        if path:
            cmd += ["-f", path]
        if db:
            cmd += [db]
        p = self._popen(cmd, env=self.getEnvironment())
        p.wait()

    def getEnvironment(self, env=None):
        if env is None:
            env = os.environ.copy()
        env['PGPORT'] = self.PGPORT
        env['PGHOST'] = self.PGHOST
        env['PGDATA'] = self.PGDATA
        if self.PGUSER:
            env['PGUSER'] = self.PGUSER
        if self.PGDATABASE:
            env['PGDATABASE'] = self.PGDATABASE
        return env

    def createUser(self, user):
        self.psql("template1", "create user \"%s\" with createdb;" % (user))
        self.PGUSER = user

    def createDatabase(self, database):
        self.psql("template1", "create database \"%s\";" % (database))
        self.PGDATABASE = database

    def parseDatabase(self, sqlfile):
        "Extract the name of the test database from the SQL file."
        with open(sqlfile, "r") as sql:
            matches = re.search(r'CREATE DATABASE "([^"]+)"', sql.read())
            if matches:
                self.PGDATABASE = matches.group(1)

    def setupAircraftDatabase(self, sqlfile=None):
        self.start()
        self.createUser('ads')
        self.createDatabase('real-time')
        if sqlfile:
            with open(sqlfile) as sf:
                p = self._popen(["psql", "template1"], stdin=sf)
                p.communicate()
            self.parseDatabase(sqlfile)
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
        # Update PGDATABASE to the name of the database just created, so
        # programs can connect to the test database without knowing the
        # actual name.
        env['ENV'].update(self.getEnvironment({}))
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
    from SCons.Script import BUILD_TARGETS
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


_usage = """\
Usage: postgres_testdb.py {init|start|stop|env|aircraft}

init      Create the data directory and config file, but do not start it.
start     Start the Postgres server running in the background.
stop      Stop the Postgres server.
env       Print the environment variables for connecting to the test
          database, suitable for sh 'eval'.
aircraft  Setup an aircraft user (ads) and database (real-time) for the
          currently running Postgres instance.
dump <sqlfile>
          Dump the current database to <sqlfile>.
"""

def main():
    "Provide access to testdb methods from the shell command-line."

    # Settings like the user and database names get set only after they are
    # explicitly created or else when a SQL file is loaded, but they do not
    # persist to the next time this script runs.  So load the settings for
    # every session, but then save them after they might have changed so
    # they can persist across runs.
    pg = PostgresTestDB()
    pg.loadSetup()
    import sys
    args = sys.argv
    op = args[1]
    if op == "init":
        pg.init()
    elif op == "start":
        pg.start()
    elif op == "stop":
        pg.stop()
    elif op == "aircraft":
        pg.setupAircraftDatabase()
        pg.saveSetup()
    elif op == "dump":
        pg.dump(args=args[2:])
    elif op == "env":
        env = pg.getEnvironment({})
        for k,v in env.items():
            sys.stdout.write("export %s=%s; " % (k, v))
        sys.stdout.write("\n")
    else:
        print(_usage)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
