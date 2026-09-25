# -*- coding: utf-8 -*-
# Sisuthros nightly QA: console errors, 390px overflow, FPS, hero terminal live replay
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

URL = "file:///C:/Users/Ismael/sisuthros.github.io/index.html"
results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    errors = []
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL, wait_until='networkidle')
    page.wait_for_timeout(1000)

    # 1. Hero terminal live replay — command typing
    typed_early = page.evaluate("document.getElementById('termTyped').textContent")
    page.wait_for_timeout(2500)  # let typing + first steps run
    state1 = page.evaluate("""(() => {
      const typed = document.getElementById('termTyped').textContent;
      const live = document.getElementById('termLive');
      return {typed, lines: live.children.length,
              lineTexts: Array.from(live.children).map(d => d.textContent)};
    })()""")
    results['terminal_mid'] = {'typed_early_len': len(typed_early), **state1}

    # wait for full sequence (typing ~1.5s + steps ~2.6s + verdict)
    page.wait_for_timeout(3500)
    state2 = page.evaluate("""(() => {
      const live = document.getElementById('termLive');
      const verdict = live.querySelector('.verdict-line');
      const cursorParent = document.getElementById('termCur').parentElement;
      return {lines: live.children.length,
              verdict: verdict ? verdict.textContent : null,
              cursor_on_last_line: cursorParent === live.lastElementChild,
              typed_full: document.getElementById('termTyped').textContent};
    })()""")
    results['terminal_final'] = state2

    # 2. Replay click
    page.click('#heroTerm')
    page.wait_for_timeout(400)
    state3 = page.evaluate("""(() => ({
      typed_reset_len: document.getElementById('termTyped').textContent.length,
      live_reset: document.getElementById('termLive').children.length
}))()""")
    results['replay_click'] = state3
    page.wait_for_timeout(6000)  # let the second run finish for the screenshot

    # 3. FPS measurement (RAF-based, 3s)
    fps = page.evaluate("""new Promise(res => {
      let frames = 0; const t0 = performance.now();
      (function cnt(){ frames++; if(performance.now() - t0 < 3000) requestAnimationFrame(cnt);
        else res(Math.round(frames / ((performance.now() - t0) / 1000))); })();
    })""")
    results['fps'] = fps

    # 4. Desktop screenshot for gemma
    page.screenshot(path='C:/Users/Ismael/sisuthros.github.io/.qa-desktop.png')

    # 5. Mobile 390px: overflow + console errors + terminal runs
    mob = browser.new_page(viewport={'width': 390, 'height': 844})
    mob_errors = []
    mob.on('console', lambda m: mob_errors.append(m.text) if m.type == 'error' else None)
    mob.on('pageerror', lambda e: mob_errors.append(str(e)))
    mob.goto(URL, wait_until='networkidle')
    mob.wait_for_timeout(1500)
    overflow = mob.evaluate("({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")
    mob.wait_for_timeout(6500)
    mob_state = mob.evaluate("""(() => ({
      verdict: (document.querySelector('#termLive .verdict-line')||{}).textContent || null,
      lines: document.getElementById('termLive').children.length
}))()""")
    mob.screenshot(path='C:/Users/Ismael/sisuthros.github.io/.qa-mobile.png')
    results['mobile'] = {'overflow': overflow, 'sw_equals_cw': overflow['sw'] == overflow['cw'],
                         'terminal': mob_state, 'errors': mob_errors}
    results['console_errors'] = errors
    browser.close()

print(json.dumps(results, indent=2, ensure_ascii=False))
ok = (not errors and not mob_errors
      and results['mobile']['sw_equals_cw']
      and fps >= 50
      and state2['verdict'] and 'VERIFIED' in state2['verdict']
      and state2['cursor_on_last_line']
      and results['terminal_mid']['lines'] >= 1
      and len(results['terminal_mid']['typed']) > 20
      and state3['live_reset'] == 0)
print('GATE:', 'PASS' if ok else 'FAIL')