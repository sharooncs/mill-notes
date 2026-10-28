import asyncio, subprocess, time, sys, os, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8768', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
JPEG = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q=="
async def main():
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8768/sharoon/'); await pg.wait_for_timeout(1500)
        await pg.evaluate("""(async () => {
          const T = Date.now() - 3600e3;
          const audio = new Blob([new Uint8Array(4000)], {type: 'audio/mp4'});
          const recId = await add('notes', {meetingId: 2, type: 'audio', kind: 'meeting', blob: audio, createdAt: T, by: 'Sharoon', duration: 600, marks: [{t: 118, tag: 'Photo'}], tags: []});
          const jpg = await (await fetch('data:image/jpeg;base64,""" + JPEG + """')).blob();
          await add('notes', {meetingId: 2, type: 'photo', blob: jpg, createdAt: T + 120000, by: 'Sharoon', text: '', tags: []});
          const n = (await getAll('notes')).find(x => x.type === 'audio');
          await put('results', {path: `results/notes/${uidOf(n)}.json`, sha: 'x', data: {uid: uidOf(n), status: 'done', kind: 'meeting', meetingId: 2, language: 'en+zh',
            summary: {headline: 'Furnace walkthrough'}, transcript: [{t0: 110, t1: 125, src: '这是装料口'}], translation: [{t0: 110, t1: 125, en: 'This is the loading door, 2.6 metres wide.'}]}});
          await loadState(); location.hash = '#m2'; render();
        })()""")
        await pg.wait_for_timeout(1000)
        mom = await pg.text_content('.note-card .moment') if await pg.query_selector('.note-card .moment') else ''
        print('photo card moment:', mom.strip().replace('\n', ' ')); ok &= '2:00' in mom and 'loading door' in mom
        strip = await pg.eval_on_selector_all('.pstrip figure', 'e => e.length'); print('photo strip in recording summary:', strip); ok &= strip == 1
        await pg.screenshot(path='/tmp/claude-0/t_photos.png', full_page=True)
        await pg.evaluate("openReport('visit', 2)"); await pg.wait_for_timeout(2500)
        html = await pg.evaluate("rpt.html")
        cap = 'At 2:00 in the meeting recording' in html and 'loading door' in html
        print('report caption has moment + quote:', cap); ok &= cap
        print('page errors:', errs); ok &= not errs; await b.close()
    print('PASS' if ok else 'FAIL')
asyncio.run(main()); srv.terminate()
