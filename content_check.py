#!/usr/bin/env python3
"""Offline editorial front-matter QA. Never edits input files."""
import argparse, datetime, hashlib, html, json, re, sys
from pathlib import Path
import yaml
from yaml.tokens import AliasToken, AnchorToken

class StrictSafeLoader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    result = {}
    for keynode, valnode in node.value:
        key = loader.construct_object(keynode, deep=deep)
        if not isinstance(key, str):
            raise ValueError('YAML 键必须是字符串')
        if key in result:
            raise ValueError('YAML 重复键：' + key)
        result[key] = loader.construct_object(valnode, deep=deep)
    return result
StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def inspect_text(text):
    errors = []
    lines = text.lstrip('\ufeff').splitlines()
    if not lines or lines[0].strip() != '---':
        return None, ['缺少开头 YAML front matter（---）']
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        return None, ['front matter 缺少结束 ---']
    raw = '\n'.join(lines[1:end])
    if len(raw.encode('utf-8')) > 16384:
        return None, ['front matter 超过 16 KiB 限额']
    try:
        if any(isinstance(t, (AliasToken, AnchorToken)) for t in yaml.scan(raw)):
            return None, ['不支持 YAML 锚点或别名，请展开后提交']
        data = yaml.load(raw, Loader=StrictSafeLoader)
    except (yaml.YAMLError, ValueError, RecursionError):
        return None, ['YAML 解析失败：语法、重复键或不支持的类型；请检查原稿']
    if not isinstance(data, dict):
        return None, ['front matter 必须是键值对象']
    for key in ('title', 'author'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(key + ' 必须是非空字符串')
    slug = data.get('slug')
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        errors.append('slug 仅支持小写英文、数字和中间短横线')
    tags = data.get('tags')
    if not isinstance(tags, list) or not tags or any(not isinstance(t, str) or not t.strip() for t in tags):
        errors.append('tags 必须是非空字符串列表')
    if type(data.get('draft')) is not bool:
        errors.append('draft 必须是 true 或 false（不带引号）')
    date = data.get('date')
    try:
        if isinstance(date, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            datetime.date.fromisoformat(date)
        elif type(date) is not datetime.date:
            raise ValueError()
    except ValueError:
        errors.append('date 必须是有效 YYYY-MM-DD 日期')
    if not '\n'.join(lines[end+1:]).strip():
        errors.append('正文为空')
    return slug if isinstance(slug, str) else None, errors

def audit(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('输入必须是存在的目录')
    records, seen = [], {}
    for path in sorted(root.rglob('*.md')):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            continue
        if path.stat().st_size > 2_000_000:
            records.append({'file': str(path.relative_to(root)), 'sha256': None, 'errors': ['文件超过 2 MB 限额']})
            continue
        payload = path.read_bytes()
        try:
            slug, errors = inspect_text(payload.decode('utf-8-sig'))
        except UnicodeError:
            slug, errors = None, ['不是有效 UTF-8 文本']
        record = {'file': str(path.relative_to(root)), 'sha256': hashlib.sha256(payload).hexdigest(), 'errors': errors}
        records.append(record)
        if slug:
            if slug in seen:
                errors.append('slug 与 ' + seen[slug]['file'] + ' 重复')
                seen[slug]['errors'].append('slug 与 ' + record['file'] + ' 重复')
            else:
                seen[slug] = record
    return {'files': len(records), 'failed': sum(bool(r['errors']) for r in records), 'records': records}

def main():
    parser = argparse.ArgumentParser(description='本地 Markdown 发布前质检；不会修改原稿')
    parser.add_argument('input_dir')
    parser.add_argument('--output', required=True, help='新建结果目录；已存在则拒绝覆盖')
    args = parser.parse_args()
    try:
        report = audit(args.input_dir)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=False)
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        rows = ''.join('<tr><td>'+html.escape(r['file'])+'</td><td>'+html.escape('；'.join(r['errors']) or '通过')+'</td></tr>' for r in report['records'])
        page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>稿件质检报告</title><style>body{font-family:system-ui;margin:40px;max-width:1000px;color:#152b3c}h1{color:#15645c}td,th{padding:16px;text-align:left;border-bottom:1px solid #ddd}table{width:100%;border-collapse:collapse}small{color:#64748b}</style><h1>稿件发布前质检</h1><p>检查 '+str(report['files'])+' 份 · 异常 '+str(report['failed'])+' 份</p><small>仅检查约定元数据结构，不代表内容准确性或平台发布成功。</small><table><tr><th>文件</th><th>结果 / 修正建议</th></tr>'+rows+'</table></html>'
        (output/'report.html').write_text(page, encoding='utf-8')
        print(json.dumps({'files': report['files'], 'failed': report['failed'], 'output': str(output)}, ensure_ascii=False))
        return 1 if report['failed'] or not report['files'] else 0
    except (OSError, ValueError) as exc:
        print('错误：'+str(exc), file=sys.stderr)
        return 2
if __name__ == '__main__':
    sys.exit(main())
