# To run the tests with py.test:
#
# env PYTHONPATH=/usr/lib/scons py.test datafilecache.py

import os
from pathlib import Path
from eol_scons.datafilecache import DataFileCache


def test_datafilecache(tmpdir):
    dfcache = DataFileCache(str(tmpdir))
    assert dfcache.getCachePath() == [str(tmpdir)]
    assert dfcache.localDownloadPath() == str(tmpdir)

    dfcache.setPrefix('rafdata:/scr/raf_data')
    target = 'DEEPWAVE/DEEPWAVErf01.kml'
    hippopath = dfcache.getFile(target)
    xpath = str(tmpdir.join(target))
    assert hippopath == xpath
    assert not os.path.exists(xpath)
    assert dfcache.getFile(target) == xpath

    dfcache.enableDownload(False)
    assert not dfcache.download(target)
    assert not os.path.exists(xpath)

    dfcache.echo = True
    dfcache.enableDownload(True)
    # return will be None because echo enabled
    assert dfcache.download(target) is None
    xcmd = f"rsync -tv rafdata:/scr/raf_data/{target} {tmpdir}/{target}"
    assert dfcache.rsync_command == xcmd
    # assert os.path.exists(xpath)
    dfcache.echo = False

    # fake the file exists in the cache
    cfile = Path(f"{tmpdir}/{target}")
    cfile.write_text("Fake cached file.\n")
    dfcache.enableDownload(False)
    assert dfcache.download(target)

    dfcache = DataFileCache(str(tmpdir))
    dfcache.setPrefix('rafdata:/scr/raf_data')
    dfcache.insertCachePath("/tmp")
    assert dfcache.getFile(target) == xpath


def test_cachepaths():
    dfcache = DataFileCache()
    dfcache.appendCachePath("/abc")
    assert dfcache.localDownloadPath() == "/abc"
    assert not os.path.exists("/abc")
    dfcache.appendCachePath("/xyz")
    assert dfcache.localDownloadPath() == "/xyz"
    assert not os.path.exists("/xyz")
    dfcache.insertCachePath("/tmp")
    assert dfcache.localDownloadPath() == "/tmp"

    assert dfcache.getFile("anyfile") == "/tmp/anyfile"

    dfcache.setDataCachePath("~")
    assert dfcache.localDownloadPath() == os.getenv('HOME')
