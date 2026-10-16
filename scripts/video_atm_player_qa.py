"""Smoke test do player: reprodução, seek e layout móvel em Chromium."""
from pathlib import Path
import functools, http.server, threading, json, re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def copyfile(self,source,outputfile):
        try: super().copyfile(source,outputfile)
        except (ConnectionResetError,BrokenPipeError): pass
    def do_GET(self):
        file=Path(self.translate_path(self.path))
        match=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers.get('Range',''))
        if file.suffix=='.mp4' and file.is_file() and match:
            size=file.stat().st_size;start=int(match[1]);end=min(int(match[2]) if match[2] else size-1,size-1)
            self.send_response(206);self.send_header('Content-Type','video/mp4')
            self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.end_headers()
            with file.open('rb') as f:
                f.seek(start)
                try:self.wfile.write(f.read(end-start+1))
                except (ConnectionResetError,BrokenPipeError):pass
        else: super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',8892),functools.partial(Quiet,directory=str(ROOT/'docs')))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        page=browser.new_page(viewport=dict(width=1440,height=1000))
        page.goto('http://127.0.0.1:8892/video.html',wait_until='domcontentloaded')
        page.wait_for_function('document.querySelector("video").readyState>=1',timeout=60000)
        meta=page.evaluate('''() => { const v=document.querySelector('video'); return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,source:v.currentSrc}; }''')
        assert meta['duration']==100 and meta['width']==1920 and meta['height']==1080,meta
        page.evaluate('''async () => {const v=document.querySelector('video');v.muted=true;await v.play();}''')
        page.wait_for_function('document.querySelector("video").currentTime>1',timeout=15000)
        page.evaluate('''() => {const v=document.querySelector('video');v.pause();v.currentTime=71;}''')
        page.wait_for_function('document.querySelector("video").readyState>=2 && !document.querySelector("video").seeking && Math.abs(document.querySelector("video").currentTime-71)<0.1',timeout=30000)
        page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        assert page.evaluate('document.querySelector("video").error') is None
        page.screenshot(path=str(ROOT/'entregas/atm-2026/revisao-player-desktop.png'))
        page.set_viewport_size(dict(width=390,height=844))
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(ROOT/'entregas/atm-2026/revisao-player-mobile.png'))
        result=dict(**meta,reproduziu=True,seek_segundo=71,layout_mobile_sem_overflow=True)
        (ROOT/'entregas/atm-2026/player-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result))
        browser.close()
finally:
    server.shutdown()
