
import eol_scons.postgres.testdb as testdb


def test_testdb_sanitize():
    tdb = testdb.PostgresTestDB()
    tdb.dryrun = True
    tdb.createUser('ads', 'password')
    assert tdb.PGUSER == 'ads'
    xcmd = ["psql", "template1", "-c",
            'CREATE USER "ads" WITH PASSWORD \'password\' CREATEDB;'
            ]
    assert tdb.last_command == xcmd
    assert tdb.password == 'password'
    xs = ("psql template1 -c CREATE USER \"ads\" "
          "WITH PASSWORD '*****' CREATEDB;")
    assert tdb._sanitized_cmd(tdb.last_command) == xs
