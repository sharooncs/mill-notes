import asyncio, subprocess, time, sys, os
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8770', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
JPEG = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q=="
async def main():
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        # 28 Oct 11:32 China time: Curve slot 09:15–11:30 just ended, checked in at Longray 11:22
        await c.add_init_script("{ const T = Date.UTC(2026, 9, 28, 3, 32); const D = Date; Date = class extends D { constructor(...a){ super(...(a.length ? a : [T + (D.now() - window.__t0)])); } static now(){ return T + (D.now() - window.__t0); } }; window.__t0 = D.now(); }")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8770/sharoon/'); await pg.wait_for_timeout(1500)
        before = await pg.evaluate("currentMeeting().m.name")
        await pg.evaluate("(async () => { await patchMeeting(5, {checkedIn: true, at: Date.now() - 2*3600e3, by: 'Sharoon'}); await patchMeeting(6, {checkedIn: true, at: Date.now() - 10*60e3, by: 'Sharoon'}); })()")
        after = await pg.evaluate("currentMeeting()")
        print('schedule pick:', before, '| with Longray check-in:', after['m']['name'], after['why']); ok &= before == 'Curve Roll Grinder' and after['m']['name'] == 'Longray Furnaces'
        await pg.evaluate("""(async () => {
          const T = Date.now() - 600e3;
          await add('notes', {meetingId: 5, type: 'audio', kind: 'meeting', blob: new Blob([new Uint8Array(4000)], {type: 'audio/mp4'}), createdAt: T, by: 'Sharoon', duration: 300, marks: [], tags: []});
          const jpg = await (await fetch('data:image/jpeg;base64,""" + JPEG + """')).blob();
          await add('notes', {meetingId: 5, type: 'photo', blob: jpg, createdAt: T + 60e3, by: 'Sharoon', text: '', tags: []});
          await loadState(); location.hash = '#m5'; render(); })()""")
        await pg.wait_for_timeout(800)
        aid = await pg.evaluate("(async () => (await getAll('notes')).find(n => n.type === 'audio').id)()")
        await pg.click(f'.note-card[data-id="{aid}"] [data-a="move"]'); await pg.wait_for_timeout(300)
        await pg.select_option(f'#mv-{aid}', '6'); chk = await pg.is_checked(f'#mvd-{aid}')
        await pg.screenshot(path='/tmp/claude-0/t_move.png')
        await pg.click(f'.note-card[data-id="{aid}"] [data-mv="go"]'); await pg.wait_for_timeout(800)
        where = await pg.evaluate("(async () => (await getAll('notes')).map(n => [n.type, n.meetingId]))()")
        print('also-move ticked:', chk, '| after move:', where); ok &= chk and all(m == 6 for _, m in where)
        snap = await pg.evaluate("(async () => stateSnapshot(await getAll('notes')).notes.map(n => n.meetingId))()"); ok &= all(m == 6 for m in snap)
        print('page errors:', errs); ok &= not errs; await b.close()
    print('PASS' if ok else 'FAIL')
asyncio.run(main()); srv.terminate()
