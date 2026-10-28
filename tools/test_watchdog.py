import asyncio, subprocess, time, sys
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '-d', __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
async def main():
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])
        c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai', permissions=['microphone'])
        pg = await c.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/sharoon/'); await pg.wait_for_timeout(1500)
        notes = "async () => (await getAll('notes')).filter(n => n.type==='audio').map(n => ({d: n.duration, k: n.kind}))"
        # 1. normal recording: no false stall
        await pg.evaluate("startRecording(1, 'meeting')"); await pg.wait_for_timeout(25000)
        st = await pg.evaluate("({on: !!rec, stalled: rec && !!rec.stalled, chunks: rec && rec.bytes})")
        print('normal 25 s:', st); ok &= st['on'] and not st['stalled'] and st['chunks'] > 0
        await pg.evaluate("stopRecording()"); await pg.wait_for_timeout(5000)
        n1 = await pg.evaluate(notes); print('saved:', n1); ok &= len(n1) == 1 and 20 < n1[0]['d'] < 32
        # 2. phone stops delivering audio after 8 s
        await pg.evaluate("startRecording(1, 'meeting')"); await pg.wait_for_timeout(9000)
        first = await pg.evaluate("(window._r1 = rec, rec.mr.ondataavailable = () => {}, rec.recId)")
        await pg.wait_for_timeout(22000)
        st = await pg.evaluate("({on: !!rec, newRec: rec && rec.recId !== _r1.recId, why: _r1.stallWhy, toast: (document.querySelector('#toast')||{}).textContent})")
        print('after stall:', st); ok &= st['on'] and st['newRec'] and st['why'] == 'no-data'
        n2 = await pg.evaluate(notes); print('saved:', n2); ok &= len(n2) == 2 and n2[1]['d'] < 16
        await pg.screenshot(path='t_watchdog.png')
        await pg.evaluate("stopRecording()"); await pg.wait_for_timeout(5000)
        print('page errors:', errs); ok &= not errs
        await b.close()
    print('PASS' if ok else 'FAIL')
asyncio.run(main()); srv.terminate()
