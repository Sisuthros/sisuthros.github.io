import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        results = {}
        # Desktop
        page = await browser.new_page(viewport={'width':1440,'height':900})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type=='error' else None)
        await page.goto('file:///C:/Users/Ismael/AppData/Local/Temp/sisuthros.github.io/index.html', wait_until='networkidle')
        await page.wait_for_timeout(2500)
        # check h1 words revealed
        h1 = await page.inner_text('h1')
        # FPS measure
        fps = await page.evaluate("""async () => {
            let frames = 0; const t0 = performance.now();
            await new Promise(r => requestAnimationFrame(function loop(){ frames++; if(performance.now()-t0 < 1000) requestAnimationFrame(loop); else r(); }));
            return frames;
        }""")
        # horizontal overflow check
        overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        results['desktop'] = {'h1': h1, 'fps': fps, 'overflow': overflow, 'errors': errors}
        await page.screenshot(path='/tmp/sisuthros.github.io/desktop.png', full_page=False)
        await page.close()

        # Mobile 390
        page = await browser.new_page(viewport={'width':390,'height':844}, is_mobile=True)
        errors2 = []
        page.on('pageerror', lambda e: errors2.append(str(e)))
        page.on('console', lambda m: errors2.append(m.text) if m.type=='error' else None)
        await page.goto('file:///C:/Users/Ismael/AppData/Local/Temp/sisuthros.github.io/index.html', wait_until='networkidle')
        await page.wait_for_timeout(2000)
        overflow2 = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        results['mobile'] = {'overflow': overflow2, 'errors': errors2}
        await page.screenshot(path='/tmp/sisuthros.github.io/mobile.png', full_page=False)
        await page.close()
        await browser.close()
        print(json.dumps(results, indent=2))

asyncio.run(main())
