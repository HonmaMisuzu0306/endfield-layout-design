"""Verify source images, deduplication, and local Markdown links; build offline index."""
from pathlib import Path
from collections import Counter
import json,hashlib,re,html
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def build_index(data):
    rows=data['images'];months=Counter()
    for r in rows:
        raw=r.get('visible_date') or r.get('published_at')
        m=re.search(r'(\d{4})年(\d{2})月(\d{2})日 (\d{2}):(\d{2})',raw)
        if not m:raise ValueError(f"Missing visible date: {r['id']}")
        iso=f'{m[1]}-{m[2]}-{m[3]}T{m[4]}:{m[5]}:00+08:00'
        r['visible_at_iso']=iso;r['month']=m[2];months[m[2]]+=1
        if r.get('date_kind')=='last_edit_only_publication_unknown':r['last_edited_at_iso']=iso;r['published_at_iso']=None
        else:r['published_at_iso']=iso;r['date_kind']='published'
        r['viewed_status']='overall_visual_inspected'
    (ROOT/'references/source-index.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 官方参考来源索引','','采集日期：2026-10-12（Asia/Shanghai）。40 张不重复图片，31 条官号动态/文章；覆盖一月至十月。', '',
    '账号核验：从用户指定的 [官号动态页](https://space.bilibili.com/1265652806/dynamic) 开始，页面显示 UID 1265652806、名称「明日方舟终末地」、企业认证「《明日方舟：终末地》官方账号」。研究图仅来自其公开发布内容。', '',
    '先通过正常 Edge 浏览查看动态、永久链接、绝对日期和页面图片。部分原图使用浏览器下载或 pageAssets 保存，其余从正常浏览发现的公开 CDN 图片路径去除缩放后缀下载。没有调用 Bilibili 私有接口，没有导出 Cookie，也未遭遇登录/验证码。方法逐图记录在 JSON。未断言获得了制作方的母版；保存的是已取得并解码核实的未缩放 CDN 图片，未人为放大。', '',
    'Wiki 仅作为一月官号原帖的线索；搜索结果中的搬运、同人、AI 图、攻略图未纳入。R38—R40 是由游戏官号发布的合作设计，作为合作特例标注。', '',
    '日期规则：正常日期记为发布日期；5 条来源只显示「编辑于」，首次发布日期未知，编辑日期单独记录。表中的编辑时间不冒充发布日期。图片整体均已查看，长图的关键文字区另做局部放大。', '',
    '[离线图片画廊](gallery.html) · [机器可读索引及 SHA-256](source-index.json)', '',
    '## 每月覆盖', '', '| 月份 | 图片数 |','|---|---|']
    lines += [f'| 2026-{m} | {months[m]} |' for m in sorted(months)]
    lines+=['','## 逐图来源','','| ID / 本地图 | 名称 | 类别 | 页面显示时间 | 原帖 | 原图 / 尺寸 |','|---|---|---|---|---|---|']
    cards=[]
    for r in rows:
        local='../'+r['local_file'];when=r.get('visible_date') or r['published_at'];title=r['title']
        lines.append(f"| [{r['id']}]({local}) | {title} | {r['category']} | {when} | [动态/文章]({r['dynamic_url']}) | [图片]({r['image_url']}) / {r['width']}×{r['height']} |")
        cards.append(f'<article data-month="{r["month"]}"><a href="{local}"><img loading="lazy" src="{local}" alt="{html.escape(title)}"></a><h2>{r["id"]} · {html.escape(title)}</h2><p>{html.escape(r["category"])} · {html.escape(when)}<br>{r["width"]} × {r["height"]}</p><a href="{r["dynamic_url"]}">官号原帖</a> · <a href="{r["image_url"]}">CDN 原图</a></article>')
    (ROOT/'references/sources.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    buttons='<button data-filter="all">全部 40 张</button>'+''.join(f'<button data-filter="{m}">{int(m)}月 · {months[m]}</button>' for m in sorted(months))
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>终末地官方排版研究 · 40 图</title><style>body{margin:0;background:#f3f5ef;color:#19241f;font:15px/1.6 "Microsoft YaHei",sans-serif}header{padding:32px 5%;border-bottom:1px solid #b8c7bd}h1{font-size:30px}nav{display:flex;gap:8px;flex-wrap:wrap}button{border:1px solid #a7beb0;background:white;padding:8px 14px;cursor:pointer}main{padding:28px 5%;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}article{background:white;padding:16px;min-width:0}article img{width:100%;height:320px;object-fit:contain;background:#e3e8e1}h2{font-size:16px}a{color:#235c47}article[hidden]{display:none}</style><header><h1>终末地官方物料 · 构成研究</h1><p>2026 年 1—10 月 / 40 张。点击图像查看完整原图；编辑时间不等于首次发布日期。合作图作为特例。</p><nav>'''+buttons+'</nav></header><main>'+''.join(cards)+'''</main><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter!=='all'&&a.dataset.month!==b.dataset.filter));</script></html>'''
    (ROOT/'references/gallery.html').write_text(page,encoding='utf-8')

def main():
    data=json.loads((ROOT/'references/source-index.json').read_text(encoding='utf-8'));build_index(data)
    seen=set()
    for r in data['images']:
        assert r['status']=='downloaded_verified',r['id']
        p=ROOT/r['local_file'];digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest==r['sha256'],r['id'];assert digest not in seen,r['id'];seen.add(digest)
        with Image.open(p) as im:im.load();assert im.size==(r['width'],r['height']),r['id']
    missing=[]
    for p in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if re.match(r'^[a-z]+:',target) or target.startswith('#'):continue
            local=target.split('#')[0]
            if not (p.parent/local).exists():missing.append((str(p.relative_to(ROOT)),target))
    assert not missing,missing
    assert set(r['month'] for r in data['images'])==set(f'{m:02d}' for m in range(1,11))
    print(json.dumps({'images':len(seen),'source_posts':len({r['dynamic_url'] for r in data['images']}),'months':dict(sorted(Counter(r['month'] for r in data['images']).items())),'categories':dict(Counter(r['category'] for r in data['images'])),'local_links':'passed','source_hashes_and_decode':'passed'},ensure_ascii=False))
if __name__=='__main__':main()
