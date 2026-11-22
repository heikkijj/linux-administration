import gzip
import importlib.util
import io
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parent / 'scripts' / 'receive-portfolio-backup.py'
spec = importlib.util.spec_from_file_location('backup_receiver', MODULE_PATH)
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)


def website_archive():
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for name, content in (
            ('portfolio/app.py', b'example app'),
            ('portfolio/requirements.txt', b'example dependency'),
            ('portfolio/templates/week4.html', b'example page'),
        ):
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            archive.addfile(entry, io.BytesIO(content))
    return output.getvalue()


class BackupTests(unittest.TestCase):
    def test_backup_is_restorable_and_retention_is_limited(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            unrelated = directory / 'unrelated.tar.gz'
            unrelated.write_bytes(b'leave untouched')
            for _ in range(3):
                latest = receiver.store_backup(io.BytesIO(website_archive()), directory, 2)

            backups = [p for p in directory.iterdir() if receiver.BACKUP_NAME.fullmatch(p.name)]
            self.assertEqual(len(backups), 2)
            self.assertIn(latest, backups)
            self.assertEqual(unrelated.read_bytes(), b'leave untouched')
            with tarfile.open(latest, 'r:gz') as archive:
                self.assertEqual(archive.extractfile('portfolio/templates/week4.html').read(),
                                 b'example page')

    def test_invalid_archive_fails_without_losing_previous_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            existing = receiver.store_backup(io.BytesIO(website_archive()), directory, 2)
            with self.assertRaises((EOFError, gzip.BadGzipFile, OSError)):
                receiver.store_backup(io.BytesIO(website_archive()[:-10]), directory, 2)
            self.assertEqual(list(directory.iterdir()), [existing])

    def test_configured_retention_keeps_96_backups(self):
        data = website_archive()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for _ in range(97):
                latest = receiver.store_backup(io.BytesIO(data), directory, receiver.KEEP_BACKUPS)
            backups = [p for p in directory.iterdir() if receiver.BACKUP_NAME.fullmatch(p.name)]
            self.assertEqual(len(backups), 96)
            self.assertIn(latest, backups)

    @unittest.skipUnless(shutil.which('bash') and shutil.which('flock'), 'requires bash and flock')
    def test_failed_archive_is_not_transferred(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'portfolio').mkdir()
            home = root / 'home'
            home.mkdir()
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            (bin_dir / 'tar').write_text('#!/bin/sh\nexit 42\n')
            (bin_dir / 'ssh').write_text('#!/bin/sh\ntouch "$SENTINEL"\n')
            for name in ('tar', 'ssh'):
                (bin_dir / name).chmod(0o700)

            sender = (MODULE_PATH.parent / 'backup-website.sh').read_text()
            sender = sender.replace('/home/ubuntu', shlex.quote(str(root)))
            script = root / 'sender.sh'
            script.write_text(sender)
            environment = os.environ.copy()
            environment.update(HOME=str(home), PATH=str(bin_dir) + os.pathsep + os.defpath,
                               SENTINEL=str(root / 'ssh-called'))
            result = subprocess.run(['bash', str(script)], env=environment, check=False)

            self.assertEqual(result.returncode, 42)
            self.assertFalse((root / 'ssh-called').exists())
            state = home / '.local' / 'state' / 'portfolio-backup'
            self.assertIn('FAILED: creating archive (exit 42)', (state / 'backup.log').read_text())
            self.assertEqual(list(state.glob('.website-archive.*')), [])


if __name__ == '__main__':
    unittest.main()
