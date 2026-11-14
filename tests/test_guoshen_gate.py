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
                    '--out-dir',str(root / 'preview'),'--publish','--approval','月明 10-21 批准《半年复盘》']
            stderr = io.StringIO()
            with patch.dict('os.environ', {}, clear=True), patch.object(sys,'argv',argv), \
                 patch.object(publish,'run_md2wechat') as transport, contextlib.redirect_stderr(stderr):
                self.assertNotEqual(publish.main(),0)
                transport.assert_not_called()
            self.assertIn('guoshen',stderr.getvalue())

    def test_legacy_gate_stops_before_upload(self):
        with tempfile.TemporaryDirectory(prefix='wechat legacy gate ') as folder:
            root = Path(folder)
            source=root/'article.html';source.write_text('<p>synthetic</p>')
            cover=root/'cover.png';cover.write_bytes(b'fixture')
            legacy=root/'legacy.py';legacy.write_text('import sys\nif "--require-chain-version" in sys.argv: sys.exit("legacy gate rejects")\nprint("old unversioned pass")\n')
            argv=['publish.py','--html',str(source),'--title','测试文章','--cover',str(cover),
                  '--out-dir',str(root/'preview'),'--publish','--approval','月明批准《测试文章》',
                  '--guoshen-gate',str(legacy),'--guoshen-dir',str(root),'--guoshen-receipt',str(source)]
            stderr=io.StringIO()
            with patch.dict('os.environ', {}, clear=True),patch.object(sys,'argv',argv), \
                 patch.object(publish,'run_md2wechat') as transport,contextlib.redirect_stderr(stderr):
                self.assertNotEqual(publish.main(),0)
                transport.assert_not_called()
            self.assertIn('legacy gate rejects',stderr.getvalue())

    def test_upload_refused_without_item_approval(self):
        with tempfile.TemporaryDirectory(prefix='wechat owner gate ') as folder:
            root = Path(folder)
            source = root / 'article.html';source.write_text('<p>x</p>')
            cover = root / 'cover.png';cover.write_bytes(b'c')
            argv = ['publish.py','--html',str(source),'--title','t','--cover',str(cover),'--out-dir',str(root/'p'),'--publish']
            stderr = io.StringIO()
            with patch.dict('os.environ', {}, clear=True), patch.object(sys,'argv',argv), \
                 patch.object(publish,'run_md2wechat') as transport, contextlib.redirect_stderr(stderr):
                self.assertEqual(publish.main(),3)
                transport.assert_not_called()
            self.assertIn('--approval',stderr.getvalue())


    def test_approval_for_other_article_is_not_reused(self):
        with tempfile.TemporaryDirectory(prefix='wechat reuse gate ') as folder:
            root = Path(folder)
            source = root / 'article.html';source.write_text('<p>x</p>')
            cover = root / 'cover.png';cover.write_bytes(b'c')
            argv = ['publish.py','--html',str(source),'--title','新文章','--cover',str(cover),'--out-dir',str(root/'p'),
                    '--publish','--approval','月明批准《旧文章》']
            with patch.dict('os.environ', {}, clear=True), patch.object(sys,'argv',argv), \
                 patch.object(publish,'run_md2wechat') as transport, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(publish.main(),3)
                transport.assert_not_called()


if __name__ == '__main__':unittest.main()
