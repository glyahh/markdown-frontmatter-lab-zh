import tempfile, unittest
from pathlib import Path
from content_check import inspect_text, audit
GOOD='''---
title: 示例文章
author: 编辑甲
slug: useful-guide
tags: [教程, 实战]
draft: false
date: 2026-10-29
---
# 示例文章
这里是演示正文，不是客户资料。
'''
class Tests(unittest.TestCase):
    def test_valid(self): self.assertEqual(inspect_text(GOOD)[1], [])
    def test_missing(self): self.assertIn('缺少',inspect_text('hello')[1][0])
    def test_duplicate_key(self): self.assertTrue(inspect_text(GOOD.replace('title: 示例文章','title: 示例文章\ntitle: 重复'))[1])
    def test_wrong_types(self): self.assertEqual(len(inspect_text(GOOD.replace('draft: false','draft: "false"').replace('tags: [教程, 实战]','tags: 教程'))[1]), 2)
    def test_invalid_date(self): self.assertTrue(inspect_text(GOOD.replace('2026-10-29','2026-02-30'))[1])
    def test_anchor_rejected(self): self.assertTrue(inspect_text(GOOD.replace('author: 编辑甲','author: &a 编辑甲'))[1])
    def test_unsafe_tag_rejected(self): self.assertTrue(inspect_text(GOOD.replace('author: 编辑甲','author: !!python/object:builtins.object {}'))[1])
    def test_no_body(self): self.assertTrue(inspect_text(GOOD.split('#')[0])[1])
    def test_duplicate_slug_and_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'a.md').write_text(GOOD);(p/'b.md').write_text(GOOD)
            result=audit(p)
            self.assertEqual(result['failed'],2)
            self.assertEqual((p/'a.md').read_text(), GOOD)
    def test_html_filename_not_injected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'<test>.md').write_text(GOOD)
            self.assertEqual(audit(p)['files'],1)
if __name__ == '__main__': unittest.main(verbosity=2)
