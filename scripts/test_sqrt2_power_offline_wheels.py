"""Pure offline dependency staging must fail closed before any installation."""
from hashlib import sha256
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import sqrt2_power_offline_wheels as w


class OfflineWheelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def wheel(self,members):
        path=self.root/'test-py3-none-any.whl'
        with zipfile.ZipFile(path,'w') as archive:
            for name,value in members:archive.writestr(name,value)
        return {path.name:sha256(path.read_bytes()).hexdigest()}

    def test_exact_bytes_stage_without_hooks_and_without_global_writes(self):
        pins=self.wheel([('example/__init__.py',b'value=3\n'),('example-1.dist-info/METADATA',b'Name: example\nVersion: 1\n')])
        output=self.root/'dependencies'
        with patch.object(w,'WHEELS',pins):result=w.stage(self.root,output)
        self.assertEqual((output/'example/__init__.py').read_bytes(),b'value=3\n')
        self.assertEqual((result['files'],result['network_calls'],result['child_processes'],result['installation_hooks_executed']),(2,0,0,0))

    def test_wrong_digest_fails_before_destination_creation(self):
        pins=self.wheel([('example.py',b'pass\n')]);pins[next(iter(pins))]='0'*64
        with patch.object(w,'WHEELS',pins),self.assertRaises(ValueError):w.stage(self.root,self.root/'output')
        self.assertFalse((self.root/'output').exists())

    def test_existing_destination_is_never_overwritten(self):
        output=self.root/'output';output.mkdir();(output/'sentinel').write_bytes(b'keep')
        with self.assertRaises(ValueError):w.stage(self.root,output)
        self.assertEqual((output/'sentinel').read_bytes(),b'keep')

    def test_unsafe_paths_data_hooks_and_symlinks_are_rejected(self):
        for name in ('../escape','/absolute','a/../escape','a\\b','a//b','a/','evil.pth','x.data/purelib/a.py'):
            with self.subTest(name=name),self.assertRaises(ValueError):w.member_name(zipfile.ZipInfo(name))
        info=zipfile.ZipInfo('link');info.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError):w.member_name(info)

    def test_duplicate_archive_destinations_are_rejected(self):
        pins=self.wheel([('same.py',b'first'),('same.py',b'second')])
        with self.assertRaises(ValueError):w.collect(self.root,pins)

    def test_member_and_aggregate_limits_are_enforced(self):
        info=zipfile.ZipInfo('huge.py');info.file_size=w.MAX_MEMBER+1
        with self.assertRaises(ValueError):w.member_name(info)
        pins=self.wheel([('a.py',b'a'),('b.py',b'b')])
        with patch.object(w,'MAX_FILES',1),self.assertRaises(ValueError):w.collect(self.root,pins)
        with patch.object(w,'MAX_TOTAL',1),self.assertRaises(ValueError):w.collect(self.root,pins)

    def test_whole_wheel_symlink_is_rejected(self):
        pins=self.wheel([('a.py',b'a')]);link=self.root/'link.whl';link.symlink_to(self.root/next(iter(pins)))
        with self.assertRaises(ValueError):w.collect(self.root,{'link.whl':next(iter(pins.values()))})

    def test_file_directory_collision_fails_before_any_destination_is_created(self):
        pins=self.wheel([('package',b'file'),('package/module.py',b'pass')]);output=self.root/'out'
        with patch.object(w,'WHEELS',pins),self.assertRaises(ValueError):w.stage(self.root,output)
        self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
