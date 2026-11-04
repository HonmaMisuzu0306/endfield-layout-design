"""Offline original composition examples, PNG + editable SVG. Requires Pillow."""
import argparse, json, math, html
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FONTS={'sans':('msyh.ttc','Microsoft YaHei'),'serif':('simsun.ttc','SimSun'),'latin':('arial.ttf','Arial')}
INK='#172420'; PAPER='#f5f7f2'; MINT='#9bd9c8'; MUTED='#505e58'; LINE='#b7c8bf'

def font(kind,size):
    path=Path('C:/Windows/Fonts')/FONTS[kind][0]
    if not path.exists():raise RuntimeError(f'Font unavailable: {path}; choose and remeasure a local font before rendering')
    return ImageFont.truetype(str(path),int(size))

def wrap(text,f,width):
    result=[]
    for para in text.split('\n'):
        start=len(result)
        line=''
        for ch in para:
            if line and f.getlength(line+ch)>width:
                if ch in '，。；：！？、）》】' or line[-1] in '（《【':
                    result.append(line[:-1]);line=line[-1]+ch
                else:result.append(line);line=ch
            else:line+=ch
        if len(line)<=2 and len(result)>start and len(result[-1])>6:
            line=result[-1][-3:]+line;result[-1]=result[-1][:-3]
        result.append(line)
    assert ''.join(result)==text.replace('\n',''), 'Content loss in wrapping'
    return result

class Canvas:
    def __init__(self,w,h):
        self.w=w;self.h=h;self.im=Image.new('RGB',(w,h),PAPER);self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',f'<rect width="{w}" height="{h}" fill="{PAPER}"/>'];self.boxes=[];self.fields=[]
    def rect(self,x,y,w,h,fill):
        self.d.rectangle((x,y,x+w,y+h),fill=fill);self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
    def line(self,x1,y1,x2,y2,color=LINE,width=1):
        self.d.line((x1,y1,x2,y2),fill=color,width=width);self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
    def poly(self,pts,fill):
        self.d.polygon(pts,fill=fill);self.svg.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}"/>')
    def ellipse(self,x,y,w,h,fill=None,stroke=None,width=1):
        self.d.ellipse((x,y,x+w,y+h),fill=fill,outline=stroke,width=width)
        self.svg.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}"/>')
    def text(self,x,y,text,size=28,kind='sans',color=INK,role='body'):
        f=font(kind,size);b=f.getbbox(text);width=f.getlength(text);height=b[3]-b[1]
        # Place the glyph ink top at y; SVG baseline uses the same measured offset.
        self.d.text((x,y-b[1]),text,font=f,fill=color,stroke_width=1 if kind=='serif' else 0)
        self.svg.append(f'<text x="{x}" y="{y-b[1]+f.getmetrics()[0]}" font-family="{FONTS[kind][1]}" font-size="{size}" fill="{color}" stroke="{color}" stroke-width="{1 if kind=="serif" else 0}">{html.escape(text)}</text>')
        self.boxes.append({'text':text,'role':role,'x':x,'y':y,'width':width,'height':height,'size':size})
        if x<0 or y<0 or x+width>self.w-1 or y+height>self.h-1:raise ValueError(f'Text out of canvas: {text}')
        return height
    def paragraph(self,x,y,text,width,size=28,kind='sans',color=INK,max_height=None,role='body',leading=1.5):
        f=font(kind,size);lines=wrap(text,f,width);lh=round(size*leading);height=(len(lines)-1)*lh+(f.getbbox(lines[-1])[3]-f.getbbox(lines[-1])[1] if lines[-1] else size)
        if max_height is not None and height>max_height:raise ValueError(f'Content requires {height}px, available {max_height}px. Expand module or split into a continuation; do not remove text.')
        for i,line in enumerate(lines):self.text(x,y+i*lh,line,size,kind,color,role)
        self.fields.append({'input':text,'rendered_lines':lines,'preserved':''.join(lines)==text.replace('\n','')})
        return y+len(lines)*lh
    def save(self,path):
        # Text/text collisions are checked separately from decorative backgrounds.
        overlaps=[]
        for i,a in enumerate(self.boxes):
            for b in self.boxes[i+1:]:
                if min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])>2 and min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y'])>2:overlaps.append([a['text'],b['text']])
        if overlaps:raise ValueError(f'Text overlap: {overlaps}')
        self.im.save(path.with_suffix('.png'));path.with_suffix('.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        return {'canvas':[self.w,self.h],'text_bounds_pass':True,'text_overlap_count':len(overlaps),'content_preserved':all(f['preserved'] for f in self.fields),'text_boxes':self.boxes,'wrapped_fields':self.fields}

def art(c):
    # Original geometric weather-observation instrument and riverside planes.
    c.rect(72,170,1056,830,'#dcece5')
    c.poly([(72,765),(500,580),(920,740),(1128,535),(1128,1000),(72,1000)],'#a9cbbd')
    c.poly([(72,840),(530,729),(970,895),(1128,780),(1128,1000),(72,1000)],'#759c8b')
    c.poly([(72,924),(624,884),(850,1000),(72,1000)],'#244c3d')
    c.ellipse(650,248,416,416,fill=INK)
    c.ellipse(683,281,350,350,fill=MINT)
    c.ellipse(722,320,272,272,fill='#e8f4e9')
    c.ellipse(747,345,222,222,stroke='#548574',width=2)
    c.ellipse(792,390,132,132,fill='#4c7767')
    c.rect(834,604,46,240,INK)
    c.poly([(857,804),(730,927),(772,945),(876,844),(988,930),(1016,902)],INK)
    for j in range(5):c.line(1012,326+j*18,1050,326+j*18,'#e8f4e9',2)
    c.rect(72,170,566,672,PAPER)

def poster(spec,out,name):
    c=Canvas(1200,1600);c.rect(0,0,1200,124,INK)
    c.text(72,35,spec['brand'],24,'latin',PAPER,'brand')
    c.text(72,77,spec['eyebrow'],20,'sans',MINT,'label')
    c.text(923,37,'OPEN / 01',24,'latin',MINT,'index')
    art(c)
    title_size=86
    for candidate in (86,82,78,74,72):
        f=font('serif',candidate)
        if len(wrap(spec['title'],f,520))*round(candidate*1.18)<=350:
            title_size=candidate;break
    title_end=c.paragraph(88,215,spec['title'],520,size=title_size,kind='serif',max_height=335,role='title',leading=1.18)
    c.rect(88,title_end+20,82,7,INK)
    sub_end=c.paragraph(88,title_end+59,spec['subtitle'],495,size=23,kind='latin',max_height=100,role='subtitle',leading=1.3)
    c.paragraph(88,sub_end+33,spec['description'],495,size=28,max_height=790-(sub_end+33),color=MUTED)
    c.line(72,1045,1128,1045,INK,2)
    c.text(72,1084,'开放时间 / DATE & TIME',24,color=MUTED,role='label')
    c.text(72,1135,spec['date'],94,'latin',INK,'date')
    c.text(75,1248,spec['time'],36,'latin',INK,'time')
    c.text(72,1327,'地点 / VENUE',22,color=MUTED,role='label')
    c.paragraph(72,1371,spec['venue'],1020,32,max_height=70,role='venue')
    c.line(72,1490,1128,1490)
    c.paragraph(72,1516,spec['note'],1030,20,color=MUTED,max_height=65,role='note')
    r=c.save(out/name);r['reference_ids']=['R17','R25','R29'];r['composition']='B / original mint observation instrument'
    return r

def card(spec,out,name):
    c=Canvas(1200,900);c.rect(0,0,1200,8,MINT);c.rect(0,8,12,892,INK)
    c.text(72,42,spec['eyebrow'],22,'latin',MUTED,'label')
    c.text(970,42,'DOC / 02',22,'latin',MUTED,'index')
    c.ellipse(1010,92,80,80,stroke='#badacc',width=2)
    c.rect(1010,92,40,40,'#dcece5')
    title_size=55
    for candidate in (55,52,50,48,46,44):
        ls=wrap(spec['title'],font('serif',candidate),944)
        if len(ls)==1 or (len(ls)<=2 and len(ls[-1])>=5):title_size=candidate;break
    title_end=c.paragraph(72,94,spec['title'],944,size=title_size,kind='serif',max_height=137,role='title',leading=1.18)
    start=max(242,title_end+48)
    footer_lines=wrap(spec['note'],font('sans',20),1030);footer_height=len(footer_lines)*30
    bottom=900-42-footer_height-18
    heights=[]
    for step in spec['steps']:
        ls=wrap(step['body'],font('sans',28),828)
        heights.append(max(92,len(ls)*42+32))
    total=sum(heights)+20*(len(heights)-1)
    if start+total>bottom:raise ValueError(f'Card needs {total}px for steps but has {bottom-start}px. Expand canvas or split; all input remains intact.')
    # Distribute available air without changing the readable type size.
    gap=(bottom-start-sum(heights))/(len(heights)-1) if len(heights)>1 else 0
    y=start
    for n,(step,h) in enumerate(zip(spec['steps'],heights),1):
        c.rect(72,y,185,38,INK);c.text(87,y+6,f'{n:02d} / '+step['label'],23,color=PAPER,role='step_label')
        c.paragraph(292,y+1,step['body'],828,28,max_height=h-6,leading=1.5)
        c.line(292,y+h-10,1128,y+h-10)
        y+=h+gap
    c.line(72,bottom+13,1128,bottom+13,INK)
    c.paragraph(72,bottom+30,spec['note'],1030,20,color=MUTED,role='note')
    r=c.save(out/name);r['reference_ids']=['R09','R26','R35','R37'];r['composition']='D + label/value fields'
    return r

def contrast(a,b):
    def lum(s):
        vals=[int(s[i:i+2],16)/255 for i in (1,3,5)]
        vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
        return sum(v*k for v,k in zip(vals,[.2126,.7152,.0722]))
    x,y=sorted([lum(a),lum(b)]);return round((y+.05)/(x+.05),2)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--spec',type=Path,default=ROOT/'assets/examples/example-spec.json');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    specs=json.loads(a.spec.read_text(encoding='utf-8'));results={}
    for name,spec in specs.items():results[name]=(poster if spec['kind']=='poster' else card)(spec,a.out,name)
    ratios={'body_on_paper':contrast(INK,PAPER),'secondary_on_paper':contrast(MUTED,PAPER),'light_on_dark':contrast(PAPER,INK),'mint_on_dark':contrast(MINT,INK)}
    assert all(v>=4.5 for v in ratios.values()),ratios
    report={'font_files':{k:str(Path('C:/Windows/Fonts')/v[0]) for k,v in FONTS.items()},'contrast_ratios':ratios,'results':results,'verification_scope':'Pillow actual-font ink bounds, text/text collisions, wrapping preservation and rendered PNG. SVG needs font-matched recheck in other editors.'}
    (a.out/'geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'outputs':list(results),'contrast':ratios,'checks':'passed'},ensure_ascii=False))
if __name__=='__main__':main()
