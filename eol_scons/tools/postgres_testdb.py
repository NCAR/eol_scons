"""
Provide simple setup for an isolated PostgreSQL test database.

This tool attaches an object to the environment which serves as a proxy for
a postgres test database running in the background.  To run tests against a
live postgresql database, we want an abstraction to control the database
before, during, and after running test commands.

Here are the main methods for controlling the database:

pg = env.PostgresTestDB()

    Create the object and setup all of the parameters.  This may return
    subclasses or database objects with different personalities, so the
    test database can impersonate different kinds of databases such as
    aircraft on-board, aircraft ground, soundings, and so on.

pg.getEnvironment()

    Return the environment variables necessary to connect to the test
    database.

pg.init()

    This initializes the database, setting up the data directory and
    tweaking the postgresql.conf file to allow local connections.  Then it
    starts the database with the start() method.  Subclasses may perform
    additional initialization that must happen for that kind of database.

pg.start()

    Start the background postgres server.

pg.stop()

    Stop the background postgres server and any other background tasks
    related to this test database, such as threads for simulating real-time
    data.

pg.destroy()

    Stop the postgres server and clean up everything creatd by init().

For running the database within scons builders and testers, there are class
members which can be used in SCons action lists.  These pull the current
test database instance from the Environment and then call the corresponding
method:

action_init()
action_start()
action_stop()
action_destroy()

Since the init() and destroy() methods also take care of starting and
stopping the server, it is typically sufficient to bracket tests with just
those actions.  If the test runs successfully, then the destroy() takes
care of removing any artifacts.  Here is an example from the aeros
datastore tests:

    sql = env.File("../../../data/real-time.sql.gz")
    dbtest = env.TestLog('xtest', [testprog, sql], [
        pg.action_init, pg.action_start_realtime] +
        env.ChdirActions(["./${SOURCE.file} --log_level=all -debug all"]) +
        [pg.action_destroy])

Subclasses can provide additional actions, such as action_start_realtime()
for running the thread to simulate aircraft real-time updates.

This python module can also run as a main script.  It parses the command
line to run methods on the PostgresTestDB instance corresponding to the
current working directory.  The connection parameters like PGUSER and
PGDATABASE, which sometimes are not determined until the SQL file gets
loaded, are saved in a setup file so they can persist across shell
commands.
"""
from __future__ import print_function


import zlib
import os
import subprocess as sp
import shutil
import re
import json
import tempfile
import gzip
import time
import threading

_postgresql_conf = """
# An empty list is supposed to disable network listening.
listen_addresses = ''
# Use the data directory for unix sockets.
%(socketparam)s = '%(PGHOST)s'
"""


class PostgresTestDB(object):

    def __init__(self, cwd=None, personality="postgrestestdb"):

        # Save off the directory from which commands should operate, in
        # case there are different test databases for different directories
        # within the same source tree.
        self.cwd = cwd
        if not self.cwd:
            self.cwd = os.getcwd()

        self.PGPORT = None
        self.PGHOST = None
        self.PGDATA = None
        self.PGUSER = None
        self.PGDATABASE = None
        self.personality = personality
        self.pgversion = None
        self.settingsfile = None
        self.setupTempConnection()
        self.debug = False
        
    def _log(self, msg):
        if self.debug:
            print(msg)

    def setupTempConnection(self):
        """
        Setup the connection parameters for a database server which runs in a
        directory under /tmp keyed by a hash of the current directory and
        listening on a unix socket.
        """
        # We want the port to depend on the current directory, so it is
        # consistent between runs without colliding with other instances
        # running from other working directories.
        port = "5%s00000" % (abs(zlib.crc32(self.cwd.encode())))
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

    def connect(self):
        """
        Return a psycopg2 connection to this test database.
        """
        # import here so the whole tool does not depend on it being installed.
        import psycopg2 as ppg
        args = {}
        if self.PGDATABASE:
            args['database'] = self.PGDATABASE
        if self.PGUSER:
            args['user'] = self.PGUSER
        if self.PGHOST:
            args['host'] = self.PGHOST
        if self.PGPORT:
            args['port'] = int(self.PGPORT)
        return ppg.connect(**args)

    def getVersion(self):
        if not self.pgversion:
            p = self._popen(['initdb', '--version'], stdout=sp.PIPE)
            self.pgversion = p.communicate()[0].split()[2]
        return self.pgversion

    def init(self, sqlfile=None):
        """
        Create the PGDATA directory, setup the configuration, and start the
        postgres server.
        """
        self._log("enter init")
        self.destroy()
        print("Postgres version: %s" % (self.getVersion()))
        self._initdb()
        socketparam = "unix_socket_directories"
        if self.getVersion().startswith("8."):
            socketparam = "unix_socket_directory"
        cfile = "%s/postgresql.conf" % (self.PGDATA)
        ctext = _postgresql_conf % { "PGHOST":self.PGHOST,
                                     "socketparam":socketparam }
        with open(cfile, "w") as cf:
            cf.write(ctext)
        self.start()
        if sqlfile:
            self.loadSQL(sqlfile)
        self._log("leave init")

    def destroy(self):
        """
        Stop the postgres server and remove the data directory, cleaning up
        everything created by init().
        """
        self.stop()
        shutil.rmtree(self.PGDATA, ignore_errors=True)

    def saveSetup(self):
        """
        Save the settings to a file for use later.
        """
        with open(self.settingsfile, "w") as sfile:
            settings = {"personality":self.personality}
            json.dump(self.getEnvironment(settings), sfile)
            sfile.write("\n")

    def loadSetup(self):
        """
        Restore settings from the settings file.
        """
        if os.path.exists(self.settingsfile):
            with open(self.settingsfile) as sfile:
                self.__dict__.update(json.load(sfile))

    def start(self):
        """
        Start the background postgres server.

        If it is already running then this will print errors and will not
        affect the running server.
        """
        self._run(["pg_ctl", "-w", "-o", "-i", "start"])

    def stop(self):
        """
        Stop the background postgres server.
        """
        self._run(["pg_ctl", "-m", "fast", "-w", "stop"])

    def _popen(self, cmd, env=None, **args):
        scmd = " ".join(cmd)
        print("Running: %s" % (scmd))
        if not env:
            env = self.getEnvironment()
        try:
            return sp.Popen(cmd, shell=False, env=env, **args)
        except Exception as ex:
            print("   *** Exception: %s: %s" % (str(ex), scmd))
            raise

    def _run(self, cmd, env=None):
        scmd = " ".join(cmd)
        p = self._popen(cmd, env=env)
        retcode = p.wait()
        if retcode:
            print("   *** Non-zero exit status: %s" % (scmd))

    def _initdb(self):
        self._run(["initdb"])

    def _psql(self, database, command):
        self._run(["psql", database, "-c", command])

    def dump(self, host=None, user=None, db=None, path=None, env=None, args=None):
        """
        Write SQL dump of @p user, @p host, @p db to @p path.  If env is None,
        then use the environment for this PostgresTestDB instance, dump the
        temporary test database.  Otherwise, pass env as os.environ or an
        empty dictionary to prevent using this object's environment
        settings.
        """
        if not db:
            db = self.PGDATABASE
        if env is None:
            env = self.getEnvironment()
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
        self._run(cmd, env=env)

    def getEnvironment(self, env=None):
        """
        Return a dictionary with environment settings for connecting to this
        database.  If env is None, then the dictionary includes all the
        current environment settings, suitable for passing to a subprocess
        call.  To get just the connection parameters, pass an empty
        dictionary, as in getEnvironment({}).
        """
        if env is None:
            env = os.environ.copy()
        env['PGPORT'] = self.PGPORT
        env['PGHOST'] = self.PGHOST
        env['PGDATA'] = self.PGDATA
        if self.PGUSER:
            env['PGUSER'] = self.PGUSER
        elif 'PGUSER' in env:
            del env['PGUSER']
        if self.PGDATABASE:
            env['PGDATABASE'] = self.PGDATABASE
        elif 'PGDATABASE' in env:
            del env['PGDATABASE']
        return env

    def createUser(self, user):
        # In case PGUSER has already been set in the environment from a
        # previous run, we need to explicitly unset it to connect as the
        # admin user.
        self.PGUSER = None
        self._psql("template1", "create user \"%s\" with createdb;" % (user))
        self.PGUSER = user

    def createDatabase(self, database):
        self._psql("template1", "create database \"%s\";" % (database))
        self.PGDATABASE = database

    def _opensql(self, sqlfile):
        if sqlfile.endswith(".gz"):
            print("opening sql file with gzip...")
            tfile = tempfile.TemporaryFile()
            gz = gzip.open(sqlfile, "r")
            tfile.writelines(gz)
            gz.close()
            tfile.seek(0)
            return tfile
        return open(sqlfile, "r")

    def parseDatabase(self, sqlfile):
        "Extract the name of the test database from the SQL file."
        with self._opensql(sqlfile) as sql:
            matches = re.search(r'CREATE DATABASE "([^"]+)"', sql.read())
            if matches:
                self.PGDATABASE = matches.group(1)

    def loadSQL(self, sqlfile):
        with self._opensql(sqlfile) as sf:
            p = self._popen(["psql", "template1"], stdin=sf)
            p.communicate()
        self.parseDatabase(sqlfile)


    def action_init(target, source, env):
        pg = env.PostgresTestDB()
        pg._log("enter action_init")
        # Look for an optional SQL source to load.
        sql = [s for s in source 
               if str(s).endswith('.sql') or str(s).endswith('.sql.gz')]
        #if not sql:
        #    raise SCons.Errors.StopError, "No SQL source."
        sqlfile = None
        if sql:
            sqlfile = sql[0]
        pg.init(sqlfile.get_abspath())
        # Update PGDATABASE to the name of the database just created, so
        # programs can connect to the test database without knowing the
        # actual name.
        env['ENV'].update(pg.getEnvironment({}))
        pg._log("leave action_init")
        return 0

    action_init = staticmethod(action_init)


    def action_start(target, source, env):
        pg = env.PostgresTestDB()
        pg.start()
        return 0

    action_start = staticmethod(action_start)


    def action_stop(target, source, env):
        pg = env.PostgresTestDB()
        pg.stop()
        return 0

    action_stop = staticmethod(action_stop)

    def action_destroy(target, source, env):
        pg = env.PostgresTestDB()
        pg.destroy()
        return 0

    action_destroy = staticmethod(action_destroy)



class AircraftTestDB(PostgresTestDB):
    """A PostgresTestDB where the user is always ads and the default database
    name is real-time, and there is a method to simulate real-time updates.
    This test database adds two action methods for controlling the realtime
    updates thread: start_realtime and stop_realtime.
    """

    def __init__(self, cwd=None):
        PostgresTestDB.__init__(self, cwd, "aircrafttestdb")
        self.realtime_thread = None
        self.stopevent = None

    def init(self, sqlfile=None):
        PostgresTestDB.init(self)
        self.createUser('ads')
        self.createDatabase('real-time')
        if sqlfile:
            self.loadSQL(sqlfile)

    def stop(self):
        self.stopRealtime()
        PostgresTestDB.stop(self)

    def simulate_realtime(self):
        """
        Loop through the times in the database until stopevent is true.
        """
        # Get a connection to the database
        db = self.connect()

        # Grab the first datetime in the raf_lrt table, then loop through
        # setting EndTime to the next greater time.
        cursor = db.cursor()
        cursor.execute("""
    SELECT datetime FROM raf_lrt ORDER BY datetime;
    """)
        rows = cursor.fetchall()
        # Skip the first few rows so the time span never appears empty.
        for r in rows[5:]:
            when = r[0]
            print("setting EndTime to %s" % (when))
            cursor.execute("""
    UPDATE global_attributes SET value = %s WHERE key = 'EndTime';""", (when,))
            # The commit is required for the notification to happen.
            db.commit()
            # In python 2.7 wait() returns true unless it times out, while
            # python 2.6 it always returns None.  So to be backwards compatible
            # we must always test whether the event is set or not.
            if self.stopevent is None:
                time.sleep(1)
            elif self.stopevent.wait(1) or self.stopevent.is_set():
                print("stop event received.")
                break
        db.close()

    def startRealtime(self, block=False):
        if block:
            self.simulate_realtime()
            return
        self.stopevent = threading.Event()
        self.realtime_thread = threading.Thread(
            target=self.simulate_realtime)
        # Mark it as a daemon so it does not prevent python from exiting if
        # scons bails somewhere else.
        self.realtime_thread.daemon = True
        self.realtime_thread.start()

    def stopRealtime(self):
        if self.realtime_thread:
            print("stopping aircraft real-time data thread...")
            self.stopevent.set()
            self.realtime_thread.join(5)
            # If it doesn't stop we don't really care.
            self.realtime_thread = None
            self.stopevent = None

    def action_start_realtime(target, source, env):
        # Run a thread to simulate real-time on the database.
        pg = env.PostgresTestDB()
        pg.startRealtime()
        return 0

    action_start_realtime = staticmethod(action_start_realtime)

    def action_stop_realtime(target, source, env):
        pg = env.PostgresTestDB()
        pg.stopRealtime()
        return 0

    action_stop_realtime = staticmethod(action_stop_realtime)




def dumpdb(target, source, env):
    platform = env['AIRCRAFT']
    db = "real-time"
    if platform:
        db = db + "-" + platform
    pg = env.PostgresTestDB()
    pg.dump("eol-rt-data.fl-ext.ucar.edu", "ads", db, target[0].get_abspath(),
            env=os.environ)


def DumpAircraftSQL(env, sqltarget, aircraft):
    from SCons.Script import BUILD_TARGETS
    if [ t for t in BUILD_TARGETS if str(t).endswith(sqltarget) ]:
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
            pg = AircraftTestDB(cwd)
        else:
            pg = PostgresTestDB(cwd)
        env['POSTGRES_TESTDB'] = pg
        # Also add the connection settings to the SCons ENV so they will
        # be set when running commands.
        env['ENV'].update(pg.getEnvironment({}))
    return pg


def generate(env):
    env.AddMethod(_get_instance, "PostgresTestDB")
    env.AddMethod(DumpAircraftSQL, "DumpAircraftSQL")
    # Put the path to this script in the shell environment, so test scripts
    # can call it directly as a script.
    ptdb = os.path.join(os.path.dirname(__file__), "postgres_testdb.py")
    env.SetDefault(POSTGRES_TESTDB_PATH=ptdb)
    env['ENV']['POSTGRES_TESTDB_PATH'] = ptdb


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


_usage = """\
Usage: postgres_testdb.py {init|start|stop|env|aircraft}

init [<sqlfile>]
          Create the data directory and config file, start the database,
          and optionally load a SQL file.
start     Start the Postgres server running in the background.
stop      Stop the Postgres server.
env       Print the environment variables for connecting to the test
          database, suitable for sh 'eval'.
cshrc     Same as 'env' but for csh.
realtime  Run aircraft real-time updates on the current Postgres instance.
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

    # For now the test database personality is always the aircraft
    # database.  However, if other personalities are ever used, then it
    # will have to be set through some method here.
    # 
    pg = AircraftTestDB()
    pg.loadSetup()
    if pg.personality == "postgrestestdb":
        pg = PostgresTestDB()
    import sys
    args = sys.argv
    op = args[1]
    if op == "init":
        sqlfile = None
        if len(args) > 2:
            sqlfile = args[2]
        pg.init(sqlfile)
        pg.saveSetup()
    elif op == "start":
        pg.start()
    elif op == "stop":
        pg.stop()
    elif op == "realtime":
        pg.startRealtime(block=True)
    elif op == "dump":
        pg.dump(args=args[2:])
    elif op == "env":
        env = pg.getEnvironment({})
        for k,v in env.items():
            sys.stdout.write("export %s=%s; " % (k, v))
        sys.stdout.write("\n")
    elif op == "cshrc":
        env = pg.getEnvironment({})
        for k,v in env.items():
            sys.stdout.write('setenv %s "%s"; ' % (k, v))
        sys.stdout.write("\n")
    else:
        print(_usage)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
