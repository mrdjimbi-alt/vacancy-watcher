# -*- coding: utf-8 -*-
"""PNG-превью базы: по несколько вакансий с каждого сайта."""
import html as html_mod
import sqlite3
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
DB = sys.argv[1] if len(sys.argv) > 1 else "vacancies.db"
OUT = HERE / (sys.argv[2] if len(sys.argv) > 2 else "превью_3_сайта.png")
PER_SITE = 6

conn = sqlite3.connect(HERE / DB)
total = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]
sites = [r[0] for r in conn.execute(
    "SELECT site, COUNT(*) c FROM vacancies GROUP BY site ORDER BY c DESC")]

rows = []
for site in sites:
    rows += conn.execute(
        "SELECT site, title, company, salary, url FROM vacancies"
        " WHERE site = ? ORDER BY id LIMIT ?", (site, PER_SITE)).fetchall()

per_site_counts = dict(conn.execute(
    "SELECT site, COUNT(*) FROM vacancies GROUP BY site"))
conn.close()

body = []
for i, (site, title, company, salary, url) in enumerate(rows, 1):
    short = url.split("//")[-1]
    if len(short) > 46:
        short = short[:46] + "..."
    body.append(
        "<tr>"
        f"<td class=n>{i}</td>"
        f"<td class=site>{html_mod.escape(site)}</td>"
        f"<td>{html_mod.escape(title)}</td>"
        f"<td>{html_mod.escape(company)}</td>"
        f"<td class=s>{html_mod.escape(salary)}</td>"
        f"<td class=u>{html_mod.escape(short)}</td>"
        "</tr>"
    )

counts_line = ", ".join(f"{s}: {per_site_counts[s]}" for s in sites)
note = sys.argv[3] if len(sys.argv) > 3 else ""

page = f"""<!doctype html>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:30px; background:#fff;
         font:14px/1.45 "Segoe UI", Tahoma, sans-serif; color:#1a1a1a; }}
  h1 {{ font-size:17px; font-weight:600; margin:0 0 5px; }}
  p.meta {{ margin:0 0 20px; color:#6b6b6b; font-size:13px; }}
  table {{ border-collapse:collapse; width:100%; }}
  th {{ text-align:left; font-weight:600; font-size:12px; color:#6b6b6b;
        text-transform:uppercase; letter-spacing:.04em;
        padding:0 14px 8px 0; border-bottom:1px solid #d9d9d9; }}
  td {{ padding:9px 14px 9px 0; border-bottom:1px solid #f0f0f0;
        vertical-align:top; }}
  td.n {{ color:#a8a8a8; width:26px; }}
  td.site {{ color:#444; white-space:nowrap; }}
  td.s {{ white-space:nowrap; }}
  td.u {{ color:#1f6feb; font-size:12px; white-space:nowrap; }}
  tr:last-child td {{ border-bottom:none; }}
  p.foot {{ margin:18px 0 0; color:#6b6b6b; font-size:13px; }}
</style>
<h1>База вакансий, собранная скриптом</h1>
<p class="meta">{counts_line}. Всего {total} вакансий, дубли и повторные публикации отсеяны.{(' ' + html_mod.escape(note)) if note else ''}</p>
<table>
  <tr><th></th><th>Сайт</th><th>Название</th><th>Компания</th><th>Зарплата</th><th>Ссылка</th></tr>
  {''.join(body)}
</table>
<p class="foot">Показано по {PER_SITE} вакансии с каждого сайта из {total}. Полная выгрузка в Excel, ссылки кликабельные.</p>
"""

tmp = HERE / "_preview.html"
tmp.write_text(page, encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1240, "height": 900},
                          device_scale_factor=2)
    pg.goto(tmp.as_uri())
    pg.screenshot(path=str(OUT), full_page=True)
    browser.close()

print(f"готово: {OUT}")
