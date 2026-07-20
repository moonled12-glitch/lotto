#!/usr/bin/env python3
# 동행복권 6/45 최신 당첨번호를 받아 통계 계산 후 index.html 생성
# GitHub Actions에서 매일 자동 실행됨
import json, os, sys, urllib.request, urllib.error

# 1차: 동행복권 공식 API (자동화 요청을 차단하는 경우가 있어 실패 시 2차로 폴백)
API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
# 2차: smok95/lotto 미러 (GitHub Pages 정적 JSON, 매주 자동 갱신)
API2 = "https://smok95.github.io/lotto/results/{}.json"
HDRS = {"User-Agent": "Mozilla/5.0 (compatible; lotto-updater/1.0)"}


def _get_json(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch(n):
    """회차 n의 (정렬된 당첨번호 6개, 보너스 번호) 반환. 아직 없는 회차면 None."""
    # 1차: 동행복권 공식 API
    try:
        d = _get_json(API.format(n))
        if str(d.get("returnValue")) == "success":
            return sorted(int(d[f"drwtNo{i}"]) for i in range(1, 7)), int(d.get("bnusNo", 0))
        return None  # 공식 API가 명시적으로 '없는 회차'라고 응답
    except Exception:
        pass  # 차단/네트워크 오류 → 미러로 폴백
    # 2차: smok95/lotto 미러
    try:
        d = _get_json(API2.format(n))
        return sorted(int(x) for x in d["numbers"]), int(d.get("bonus_no", 0))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # 아직 추첨 전인 회차
        raise


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
            res = fetch(n)
        except Exception as e:
            print(f"stop at {n}: {e}")
            break
        if res is None:
            break
        nums, bonus = res
        draws[n] = nums
        latest_bonus = bonus
        latest_nums = nums
        added += 1
        n += 1
    print(f"added {added} new draw(s); latest = {max(draws)}")

    # 최신 회차 보너스 번호 확보 (신규 없으면 최신 회차 재조회)
    latest = max(draws)
    if latest_nums is None:
        res = None
        try:
            res = fetch(latest)
        except Exception:
            pass
        if res:
            latest_nums, latest_bonus = res
        else:
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
