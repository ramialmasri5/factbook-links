#!/usr/bin/env python3
from pathlib import Path
import html, json
ROOT = Path(__file__).resolve().parents[1]
BASE = "https://ramialmasri5.github.io/factbook-links"
DATA = json.loads((ROOT / "data/archive.json").read_text(encoding="utf-8"))
TPL = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,nofollow,noarchive">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{thumb}">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="720">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Fact Book">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{thumb}">
<style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}html,body{{margin:0;min-height:100%;font-family:Arial,Helvetica,sans-serif;background:#0c1016;color:#fff}}body{{min-height:100vh;display:grid;place-items:center;overflow:hidden}}.bg{{position:fixed;inset:-35px;background:url('{thumb}') center/cover no-repeat;filter:blur(24px) brightness(.42);transform:scale(1.08)}}.shade{{position:fixed;inset:0;background:linear-gradient(180deg,rgba(5,8,13,.18),rgba(5,8,13,.82))}}.card{{position:relative;z-index:2;width:min(92vw,720px);padding:28px 22px 34px;text-align:center}}.logo{{display:flex;direction:ltr;justify-content:center;align-items:center;gap:18px;margin:14px 0 30px}}.play{{width:116px;height:80px;border-radius:20px;background:#fff;display:grid;place-items:center;box-shadow:0 10px 35px rgba(0,0,0,.28)}}.play:after{{content:"";margin-left:8px;border-top:20px solid transparent;border-bottom:20px solid transparent;border-left:33px solid #111}}.yt{{font-size:64px;font-weight:800;letter-spacing:-3px}}h1{{font-size:clamp(26px,5vw,44px);line-height:1.18;margin:0 auto 30px;max-width:680px;text-shadow:0 2px 8px rgba(0,0,0,.5)}}.actions{{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;direction:ltr}}.btn{{appearance:none;border:0;border-radius:12px;padding:17px 26px;min-width:210px;font-size:24px;font-weight:700;text-decoration:none;color:#fff;box-shadow:0 7px 24px rgba(0,0,0,.3)}}.app{{background:#ff0033}}.web{{background:#5b6472}}.status{{margin-top:24px;font-size:18px;color:#edf2f7}}.small{{margin-top:12px;font-size:14px;color:#cbd5e1}}@media(max-width:540px){{.card{{padding-top:12px}}.logo{{margin-bottom:22px}}.play{{width:92px;height:64px;border-radius:17px}}.play:after{{border-top-width:16px;border-bottom-width:16px;border-left-width:27px}}.yt{{font-size:48px}}.btn{{width:100%;font-size:21px}}}}
</style>
</head>
<body>
<div class="bg"></div><div class="shade"></div>
<main class="card">
<div class="logo"><div class="play"></div><div class="yt">YouTube</div></div>
<h1>{title}</h1>
<div class="actions"><a id="appBtn" class="btn app" href="#">Open YouTube App</a><a class="btn web" href="{web}">YouTube Web</a></div>
<div id="status" class="status">جارٍ فتح تطبيق YouTube…</div>
<div class="small">إذا منع Facebook الفتح التلقائي، اضغط الزر الأحمر مرة واحدة.</div>
</main>
<script>
(function(){{
 const id={vid_json}, web={web_json};
 const ua=navigator.userAgent||'', isAndroid=/Android/i.test(ua), isIOS=/iPhone|iPad|iPod/i.test(ua);
 const android='intent://www.youtube.com/watch?v='+id+'#Intent;scheme=https;package=com.google.android.youtube;S.browser_fallback_url='+encodeURIComponent(web)+';end';
 const ios='youtube://www.youtube.com/watch?v='+id;
 const appUrl=isAndroid?android:(isIOS?ios:web);
 const btn=document.getElementById('appBtn'), status=document.getElementById('status');
 btn.href=appUrl;
 btn.addEventListener('click',function(){{status.textContent='Opening YouTube…';}});
 if(isAndroid||isIOS){{setTimeout(function(){{try{{window.location.href=appUrl}}catch(e){{status.textContent='اضغط الزر الأحمر للمتابعة.'}}}},25);setTimeout(function(){{if(!document.hidden)status.textContent='اضغط Open YouTube App إذا لم يفتح التطبيق تلقائيًا.'}},900);}}else{{status.textContent='افتح الرابط من الهاتف لتشغيل تطبيق YouTube.';}}
}})();
</script>
</body></html>'''
for v in DATA["videos"]:
    vid=v["video_id"]; slug=v["slug"]
    title=html.escape(v["title"], quote=True); desc=html.escape(v["description_ar"], quote=True)
    url=f"{BASE}/{slug}/"; thumb=f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"; web=f"https://www.youtube.com/watch?v={vid}"
    out=TPL.format(title=title,desc=desc,url=url,thumb=thumb,web=web,vid_json=json.dumps(vid),web_json=json.dumps(web))
    d=ROOT/slug; d.mkdir(exist_ok=True); (d/"index.html").write_text(out,encoding="utf-8")
print(f"generated {len(DATA['videos'])} page(s)")
