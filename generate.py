#!/usr/bin/env python3
# 동행복권 6/45 최신 당첨번호를 받아 통계 계산 후 index.html 생성
# GitHub Actions에서 매주 자동 실행됨
import json, os, sys, urllib.request

API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
HDRS = {"User-Agent": "Mozilla/5.0 (compatible; lotto-updater/1.0)"}


def fetch(n):
    req = urllib.request.Request(API.format(n), headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def load_draws():
    if os.path.exists("draws.json"):
        return {int(k): sorted(v) for k, v in json.load(open("draws.json")).items()}
    return {}


def main():
    draws = load_draws()
    start = (max(draws) + 1) if draws else 1
    n = start
    added = 0
    latest_bonus = 0
    latest_nums = None
    while True:
        try:
            d = fetch(n)
        except Exception as e:
            print(f"stop at {n}: {e}")
            break
        if str(d.get("returnValue")) != "success":
            break
        nums = sorted(int(d[f"drwtNo{i}"]) for i in range(1, 7))
        draws[n] = nums
        latest_bonus = int(d.get("bnusNo", 0))
        latest_nums = nums
        added += 1
        n += 1
    print(f"added {added} new draw(s); latest = {max(draws)}")

    # 최신 회차 보너스 번호 확보 (신규 없으면 최신 회차 재조회)
    latest = max(draws)
    if latest_nums is None:
        try:
            d = fetch(latest)
            latest_bonus = int(d.get("bnusNo", 0))
            latest_nums = sorted(int(d[f"drwtNo{i}"]) for i in range(1, 7))
        except Exception:
            latest_nums = draws[latest]
            latest_bonus = 0

    json.dump({str(k): draws[k] for k in sorted(draws)},
              open("draws.json", "w"), ensure_ascii=False)

    order = sorted(draws)

    def freq(keys):
        c = [0] * 46
        for k in keys:
            for x in draws[k]:
                c[x] += 1
        return c[1:]

    n1 = min(52, len(order))
    n5 = min(260, len(order))
    data = {
        "latestDraw": latest,
        "latestNumbers": latest_nums,
        "latestBonus": latest_bonus,
        "totalDraws": len(order),
        "n1y": n1, "n5y": n5, "nall": len(order),
        "f1y": freq(order[-n1:]),
        "f5y": freq(order[-n5:]),
        "fall": freq(order),
    }
    tpl = open("template.html", encoding="utf-8").read()
    html = tpl.replace("__LOTTO_DATA__", json.dumps(data, ensure_ascii=False))
    open("index.html", "w", encoding="utf-8").write(html)
    print("index.html generated; total draws:", len(order))


if __name__ == "__main__":
    main()
