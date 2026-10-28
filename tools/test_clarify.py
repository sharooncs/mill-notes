import asyncio, subprocess, time, sys, json
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8766', '-d', __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
RES = {"uid": "9alw04cx-55", "status": "done", "kind": "meeting", "meetingId": 2, "language": "en+zh", "summary": {"headline": "test"},
       "transcript": [], "translation": [],
       "clarify": [{"id": "9alw04cx-55-q1", "uid": "9alw04cx-55", "t": 2644, "q": "Traditional furnace load: 18 t or 80 t?",
                    "options": ["18 t", "80 t"], "context_en": "the traditional design can load 80 tons… 18 to 28 tons", "context_src": "我这个可以装到28-30", "clip": "results/clips/9alw04cx-55-q1.m4a"},
                   {"id": "9alw04cx-55-q2", "uid": "9alw04cx-55", "t": 2883, "q": "Automation system +US$10,000: per furnace or total?",
                    "options": ["Per furnace", "Total"]}]}
async def main():
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8766/sharoon/'); await pg.wait_for_timeout(1500)
        await pg.evaluate(f"(async () => {{ await put('results', {{path: 'results/notes/9alw04cx-55.json', sha: 'x', data: {json.dumps(RES)}}}); await loadSynced(); render(); }})()")
        await pg.wait_for_timeout(800)
        bar = await pg.text_content('.clarbar') if await pg.query_selector('.clarbar') else None
        print('home banner:', bar); ok &= bool(bar) and '2 questions' in bar
        await pg.screenshot(path='t_clar_home.png')
        await pg.click('.clarbar'); await pg.wait_for_timeout(800)
        n = await pg.eval_on_selector_all('.cq', 'e => e.length'); print('questions on visit page:', n); ok &= n == 2
        await pg.screenshot(path='t_clar_visit.png', full_page=False)
        await pg.click('.cq[data-qid="9alw04cx-55-q1"] [data-cans="18 t"]'); await pg.wait_for_timeout(600)
        await pg.fill('.cq[data-qid="9alw04cx-55-q2"] .other input', 'Per furnace, quoted by Troy'); await pg.click('.cq[data-qid="9alw04cx-55-q2"] [data-cother]'); await pg.wait_for_timeout(600)
        snap = await pg.evaluate("(async () => stateSnapshot(await getAll('notes')).answers)()")
        print('synced answers:', [(a['id'], a['a'], a['by']) for a in snap]); ok &= len(snap) == 2 and snap[0]['by'] == 'Sharoon'
        hdr = await pg.text_content('#clar .eyebrow'); print('card header:', hdr); ok &= 'all answered' in hdr
        await pg.reload(); await pg.wait_for_timeout(1500)
        kept = await pg.evaluate("Object.keys(answers).length"); print('answers kept after reload:', kept); ok &= kept == 2
        await pg.evaluate("location.hash = '#m2'"); await pg.wait_for_timeout(800)
        await pg.screenshot(path='t_clar_answered.png')
        print('page errors:', errs); ok &= not errs; await b.close()
    print('PASS' if ok else 'FAIL')
asyncio.run(main()); srv.terminate()
