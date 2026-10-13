import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publish


class WechatGuoshenTests(unittest.TestCase):
    def test_unreviewed_upload_stops_before_transport(self):
        with tempfile.TemporaryDirectory(prefix='wechat review gate ') as folder:
            root = Path(folder)
            source = root / 'article.html';source.write_text('<p>真实半年复盘</p>')
            cover = root / 'cover.png';cover.write_bytes(b'local cover fixture')
            argv = ['publish.py','--html',str(source),'--title','半年复盘','--cover',str(cover),
                    '--out-dir',str(root / 'preview'),'--publish']
            stderr = io.StringIO()
            with patch.dict('os.environ', {}, clear=True), patch.object(sys,'argv',argv), \
                 patch.object(publish,'run_md2wechat') as transport, contextlib.redirect_stderr(stderr):
                self.assertNotEqual(publish.main(),0)
                transport.assert_not_called()
            self.assertIn('guoshen',stderr.getvalue())


if __name__ == '__main__':unittest.main()
