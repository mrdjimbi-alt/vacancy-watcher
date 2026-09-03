# -*- coding: utf-8 -*-
"""Разведка сайта вакансий: серверный HTML или JS, где лежат карточки.

Запуск:  python probe.py <url>
Пишет рядом:  page_requests.html  (+ page_playwright.html, если нужен браузер)
"""
import re
import sys
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

VACANCY_URL = re.compile(r"/(vacanc|vakans|job|jobs|rabota|position|career)", re.I)
SALARY = re.compile(r"(\d[\d\s ]{2,})\s*(?:₽|руб|р\.|тыс)", re.I)


def fetch_requests(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    return r.status_code, r.text


def fetch_playwright(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA, locale="ru-RU")
        page.goto(url, wait_until="networkidle", timeout=60000)
        html = page.content()
        browser.close()
    return html


def analyze(html, tag):
    soup = BeautifulSoup(html, "html.parser")
    links = [a for a in soup.find_all("a", href=True) if VACANCY_URL.search(a["href"])]
    salaries = SALARY.findall(soup.get_text(" ", strip=True))

    print(f"\n=== {tag} ===")
    print(f"размер html: {len(html)} символов")
    print(f"ссылок, похожих на вакансии: {len(links)}")
    print(f"чисел, похожих на зарплату: {len(salaries)}")

    # какой класс контейнера чаще всего оборачивает такие ссылки
    classes = Counter()
    for a in links:
        for parent in list(a.parents)[:4]:
            cls = parent.get("class") if hasattr(parent, "get") else None
            if cls:
                classes[f"{parent.name}.{'.'.join(cls)}"] += 1

    if classes:
        print("\nчастые контейнеры вокруг ссылок (кандидаты в селектор карточки):")
        for sel, n in classes.most_common(12):
            print(f"  {n:>4}  {sel}")

    if links:
        print("\nпервые 5 ссылок:")
        for a in links[:5]:
            print(f"  {a.get_text(' ', strip=True)[:70]!r} -> {a['href'][:90]}")

    return len(links)


def main():
    if len(sys.argv) < 2:
        print("нужен url: python probe.py https://site.ru/vacancies")
        sys.exit(1)
    url = sys.argv[1]

    try:
        code, html = fetch_requests(url)
        print(f"requests: HTTP {code}")
        (HERE / "page_requests.html").write_text(html, encoding="utf-8")
        found = analyze(html, "requests + bs4")
    except Exception as e:
        print(f"requests упал: {e}")
        found = 0

    if found < 3:
        print("\nсерверного html мало, пробую браузер...")
        try:
            html = fetch_playwright(url)
            (HERE / "page_playwright.html").write_text(html, encoding="utf-8")
            analyze(html, "playwright")
        except Exception as e:
            print(f"playwright упал: {e}")


if __name__ == "__main__":
    main()
