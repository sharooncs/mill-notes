import asyncio, subprocess, time, sys, os, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8769', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
JPEG = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q=="
X = {"uid": "", "kind": "slide", "title": "1850 mm 铝箔轧机 主要参数", "text_src": "最大轧制速度 1500 m/min\n出口厚度 0.006 mm", "text_en": "Max rolling speed 1500 m/min\nExit thickness 0.006 mm",
     "figures": ["Max rolling speed 1500 m/min", "Exit thickness 0.006 mm"], "diagram": "", "summary": "Main parameters of the 1850 mm foil mill.", "legibility": "clear", "relevant": True}
async def main():
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8769/sharoon/'); await pg.wait_for_timeout(1500)
        await pg.evaluate("""(async (X) => {
          const jpg = await (await fetch('data:image/jpeg;base64,""" + JPEG + """')).blob();
          const id = await add('notes', {meetingId: 1, type: 'photo', blob: jpg, createdAt: Date.now(), by: 'Sharoon', text: '', tags: []});
          const n = (await getAll('notes')).find(x => x.type === 'photo'); X.uid = uidOf(n);
          await put('results', {path: `results/photos/${X.uid}.json`, sha: 'x', data: X});
          await loadState(); location.hash = '#m1'; render();
        })""", X)
        await pg.wait_for_timeout(1000)
        t = await pg.text_content('.note-card .pread') if await pg.query_selector('.note-card .pread') else ''
        print('photo card:', ' '.join(t.split())[:160]); ok &= '1500 m/min' in t and 'Claude read this slide' in t
        await pg.screenshot(path='/tmp/claude-0/t_photoread.png', full_page=True)
        await pg.evaluate("openReport('visit', 1)"); await pg.wait_for_timeout(2500)
        html = await pg.evaluate("rpt.html")
        rep = 'From slides and drawings' in html and 'Max rolling speed 1500 m/min' in html
        print('report section:', rep); ok &= rep
        print('page errors:', errs); ok &= not errs; await b.close()
    print('PASS' if ok else 'FAIL')
asyncio.run(main()); srv.terminate()
