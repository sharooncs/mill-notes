import asyncio, subprocess, time, sys, os, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # put ~30 large JPEGs in sharoon/_testimg/ first
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8771', '-d', ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
imgs = sorted(os.listdir(ROOT + '/sharoon/_testimg'))
RES = json.load(open('/home/claude/butterfly-sync/results/notes/9alw04cx-16.json'))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--js-flags=--expose-gc'])
        c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, timezone_id='Asia/Shanghai')
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8771/sharoon/'); await pg.wait_for_timeout(1500)
        await pg.evaluate("""(async ({imgs, RES}) => {
          const T = Date.now() - 3 * 3600e3;
          const rid = await add('notes', {meetingId: 1, type: 'audio', kind: 'meeting', blob: new Blob([new Uint8Array(50e6)], {type: 'audio/mp4'}), createdAt: T, by: 'Sharoon', duration: 6163, marks: [], tags: []});
          for (let i = 0; i < imgs.length; i++){ const bl = await (await fetch('_testimg/' + imgs[i])).blob();
            await add('notes', {meetingId: 1, type: 'photo', blob: bl, createdAt: T + 60e3 * (i * 3 + 1), by: 'Sharoon', text: '', tags: []}); }
          const n = (await getAll('notes')).find(x => x.type === 'audio'); RES.uid = uidOf(n);
          RES.clarify = RES.clarify.map((c, i) => ({...c, resolved: false, id: `${RES.uid}-q${i+1}`, uid: RES.uid}));
          await put('results', {path: `results/notes/${RES.uid}.json`, sha: 'x', data: RES});
          await loadState();
        })""", {'imgs': imgs, 'RES': RES})
        t = time.time(); await pg.evaluate("location.hash = '#m1'"); await pg.wait_for_timeout(3000); print('has clar', await pg.query_selector('#clar') is not None, 'cards', await pg.eval_on_selector_all('.note-card','e=>e.length'), 'hash', await pg.evaluate('location.hash'), 'res', await pg.evaluate('Object.keys(results)'), errs)
        print(f'open visit page: {time.time()-t:.2f}s')
        r = await pg.evaluate("(async () => { const t = performance.now(); await render(); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); return performance.now() - t; })()"); print(f'full re-render of the visit page: {r:.0f} ms')
        await pg.evaluate("document.querySelector('#clar').scrollIntoView()"); await pg.wait_for_timeout(1500)
        y0 = await pg.evaluate("window.scrollY"); top0 = await pg.evaluate("document.querySelector('.cq').getBoundingClientRect().top")
        imgs0 = await pg.evaluate("[...document.images].map(i => i.src).slice(0,3)")
        y_before = await pg.evaluate('window.scrollY'); await pg.evaluate("document.querySelector('.cq [data-cans]').click()")
        shots = []
        for k in range(8):
            await pg.wait_for_timeout(100)
            shots.append(await pg.evaluate("Math.round(document.querySelector('#clar').getBoundingClientRect().top)"))
        imgs1 = await pg.evaluate("[...document.images].map(i => i.src).slice(0,3)")
        print('scrollY before/after answer:', y_before, await pg.evaluate('window.scrollY'))
        print('card position before:', round(top0), 'after answer (every 100 ms):', shots)
        print('photo URLs rebuilt on answer:', imgs0 != imgs1)
        live = await pg.evaluate("urls.length"); print('object URLs held:', live)
        mem = await pg.evaluate("performance.memory ? Math.round(performance.memory.usedJSHeapSize/1e6) : -1"); print('JS heap MB', mem)
        # what moves after a redraw: heights of every block above the anchor, sampled over time
        await pg.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)"); await pg.wait_for_timeout(2500)
        H = "[...document.querySelectorAll('#view > *')].map(e => Math.round(e.getBoundingClientRect().height))"
        h0 = await pg.evaluate(H); await pg.evaluate("(async () => { await render(); })()")
        for k in range(4):
            await pg.wait_for_timeout(150); h1 = await pg.evaluate(H)
            print('changed blocks:', [(j, h0[j], h1[j]) for j in range(min(len(h0), len(h1))) if h0[j] != h1[j]][:6], 'n', len(h0), len(h1))
        print('answer probe:')
        await pg.evaluate("document.querySelector('#clar').scrollIntoView()"); await pg.wait_for_timeout(1500)
        t0 = await pg.evaluate("[window.scrollY, Math.round(document.querySelector('#clar').getBoundingClientRect().top)]")
        await pg.evaluate("document.querySelectorAll('.cq [data-cans]')[3].click()"); await pg.wait_for_timeout(500)
        t1 = await pg.evaluate("[window.scrollY, Math.round(document.querySelector('#clar').getBoundingClientRect().top)]")
        print('scrollY, card top before/after:', t0, t1)
        # a sync finishes while you are scrolled half-way down
        await pg.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)"); await pg.wait_for_timeout(1200)
        before = await pg.evaluate("(() => { const el = [...document.querySelectorAll('.note-card')].find(e => e.getBoundingClientRect().bottom > 70); return [el.dataset.id, Math.round(el.getBoundingClientRect().top)]; })()")
        src0 = await pg.evaluate("[...document.images].map(i => i.src).join()")
        await pg.evaluate("(async () => { await render(); })()"); 
        tops = []
        for k in range(6):
            await pg.wait_for_timeout(150)
            tops.append(await pg.evaluate(f"Math.round(document.querySelector('.note-card[data-id=\"{before[0]}\"]').getBoundingClientRect().top)"))
        src1 = await pg.evaluate("[...document.images].map(i => i.src).join()")
        print('sync redraw mid-page: card at', before[1], '-> after (every 150 ms):', tops, '| photos reloaded:', src0 != src1)
        # a sync finishes while you are listening to the recording
        await pg.evaluate("(() => { const a = document.querySelector('.note-card audio'); a.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='; Object.defineProperty(a, 'paused', {get: () => false}); })()")
        print('redraw held while audio plays:', await pg.evaluate("editing()"))
        print('errors', errs); await b.close()
asyncio.run(main()); srv.terminate()
