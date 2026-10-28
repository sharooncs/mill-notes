import asyncio, subprocess, time, sys, base64
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8767', '-d', __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Shanghai')
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8767/sharoon/'); await pg.wait_for_timeout(1500)
        await pg.evaluate("(async () => { await add('notes', {meetingId: 2, type: 'text', text: 'Sachsen: 28-30 t per furnace vs 18 t traditional. Ask for written price per size.', tags: ['Spec'], createdAt: Date.now(), by: 'Sharoon'}); await loadState(); })()")
        await pg.evaluate("openReport('visit', 2)"); await pg.wait_for_timeout(1500)
        await pg.click('#rpt-pdf'); 
        for _ in range(60):
            t = await pg.text_content('#rpt-pdf')
            if t.strip() != 'Making PDF…': break
            await pg.wait_for_timeout(500)
        print('button:', t)
        data = await pg.evaluate("(async () => { const b = await rpt.pdf.arrayBuffer(); let s=''; new Uint8Array(b).forEach(x => s += String.fromCharCode(x)); return [rpt.pdf.name, btoa(s)]; })()")
        open('t_report.pdf', 'wb').write(base64.b64decode(data[1])); print('file:', data[0])
        print('page errors:', errs); await b.close()
asyncio.run(main()); srv.terminate()
