from pathlib import Path
import json, threading, http.server, functools, time, io, sys
from playwright.sync_api import sync_playwright
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'entregas'/'altamira'
def main():
    port=8877 if '--base-only' in sys.argv else 8876
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(OUT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-webgl','--ignore-gpu-blocklist','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page.on('pageerror',lambda e:print('JS ERROR',e,flush=True))
        page.goto(f'http://127.0.0.1:{port}/render.html',wait_until='networkidle',timeout=120000)
        page.wait_for_function('window.ready===true',timeout=120000)
        page.wait_for_function('v.scene.globe.tilesLoaded',timeout=120000)
        page.screenshot(path=str(OUT/'paisagem.png'))
        (OUT/'projecao.json').write_text(json.dumps(page.evaluate('project()')),encoding='utf-8')
        (OUT/'creditos_imagem.txt').write_text(page.evaluate('getCredits()'),encoding='utf-8')
        print('BASE READY',flush=True)
        if '--base-only' in sys.argv:
            browser.close();server.shutdown();return
        intro=OUT/'intro_chaves';intro.mkdir(exist_ok=True)
        # 48 terrain-loaded keyframes; composition interpolates to 240 output frames.
        for i in range(48):
            page.evaluate('(u)=>setCamera(u)',i/47)
            page.wait_for_function('v.scene.globe.tilesLoaded',timeout=120000)
            page.screenshot(path=str(intro/f'{i:04d}.png'))
            if i%6==0:print('INTRO',i,'/ 48',flush=True)
        browser.close()
    server.shutdown()
if __name__=='__main__':main()
