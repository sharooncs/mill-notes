import asyncio, subprocess, time, sys, os, json, glob
from playwright.async_api import async_playwright
SYNC='/home/claude/butterfly-sync'
docs={d['device']:d for d in [json.load(open(p)) for p in glob.glob(f'{SYNC}/inbox/*/state.json')]}
res={os.path.relpath(p,SYNC):json.load(open(p)) for p in glob.glob(f'{SYNC}/results/**/*.json',recursive=True)}
srv=subprocess.Popen([sys.executable,'-m','http.server','8792','-d',os.path.dirname(os.path.dirname(os.path.abspath(__file__)))],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
COUNT="(() => { const c = {}; for (const k of [10,11,12]) c[k] = (noteCache[k]||[]).length; return c; })()"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for me in ['9alw04cx','third']:
      c=await b.new_context(timezone_id='Asia/Shanghai'); pg=await c.new_page(); await pg.add_init_script(f"localStorage.setItem('mn.device', '{me}')"); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
      await pg.goto('http://localhost:8792/sharoon/'); await pg.wait_for_timeout(1200)
      await pg.evaluate("""async ({docs, res, me}) => {
        if (me !== 'third'){ const d = docs[me]; for (const n of d.notes) await put('notes', {...n, synced: true});
          for (const m of Object.values(d.meetings)) await put('meetings', m); }
        for (const [dev, d] of Object.entries(docs)) if (dev !== me) await put('remote', {...d, device: dev});
        for (const [path, data] of Object.entries(res)) if (path !== 'results/refile.json') await put('results', {path, sha: 'x', data});
        await loadState(); }""", {'docs':docs,'res':res,'me':me})
      before=await pg.evaluate(COUNT)
      await pg.evaluate("async (r) => { await put('results', {path: 'results/refile.json', sha: 'y', data: r}); await loadState(); await loadState(); }", res['results/refile.json'])
      after=await pg.evaluate(COUNT)
      stored=await pg.evaluate("(async () => { const n = await getAll('notes'); const m = await getAll('meetings'); return [n.filter(x => x.meetingId === 11).length, n.filter(x => x.meetingId === 10).length, m.filter(x => [10,11,12].includes(x.id)).map(x => [x.id, new Date(x.at).toISOString().slice(11,16)])]; })()")
      ins=await pg.evaluate("[10,11].map(id => visitModel(id).ins.map(x => new Date(x.at).toISOString().slice(11,16)))")
      print(me,'before',before,'after',after,'stored(11,10,checkins UTC)',stored,'visit check-ins UTC',ins,'errors',errs)
    await b.close()
asyncio.run(main()); srv.terminate()
