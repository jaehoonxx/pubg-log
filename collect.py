import os
import csv
import time
import getpass
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.pubg.com/shards/steam"
MAP_NAMES = {
    "Baltic_Main": "에란겔",
    "Erangel_Main": "에란겔",
    "Tiger_Main": "태이고",
    "Neon_Main": "론도",
    "Desert_Main": "미라마",
}
DATA_DIR = "data"
OUTPUT = os.path.join(DATA_DIR, "vehicle_rides.csv")
DONE = os.path.join(DATA_DIR, "processed_matches.txt")
TARGET_ROWS = 65000
DAYS_BACK = 13
FIELDS = [
    "match_id", "map_name", "map_code", "game_mode", "match_type", "created_at",
    "vehicle_id", "vehicle_type", "seat_index", "x", "y", "z", "elapsed_time", "is_game",
]

session = requests.Session()


def get_key():
    key = os.environ.get("PUBG_API_KEY")
    if key:
        return key.strip()
    return getpass.getpass("PUBG API 키를 붙여넣고 Enter를 누르세요 (화면에 안 보이는 게 정상): ").strip()


def api_get(url, key, params=None, limited=False):
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/vnd.api+json"}
    for _ in range(5):
        r = session.get(url, headers=headers, params=params, timeout=60)
        if r.status_code == 429:
            print("  요청 한도 초과, 60초 기다립니다...")
            time.sleep(60)
            continue
        if r.status_code == 401:
            raise SystemExit("API 키가 올바르지 않습니다. 키를 다시 확인해 주세요.")
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
        if limited:
            time.sleep(6.5)
        return r.json()
    raise RuntimeError("여러 번 시도했지만 응답을 받지 못했습니다.")


def get_sample_match_ids(key, start_time=None):
    params = {"filter[createdAt-start]": start_time} if start_time else None
    data = api_get(f"{BASE}/samples", key, params=params, limited=True)
    return [m["id"] for m in data["data"]["relationships"]["matches"]["data"]]


def parse_time(s):
    s = s.rstrip("Z")
    if "." in s:
        main, frac = s.split(".")
        s = f"{main}.{(frac + '000000')[:6]}"
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")


def process_match(key, match_id):
    match = api_get(f"{BASE}/matches/{match_id}", key)
    attrs = match["data"]["attributes"]
    map_code = attrs.get("mapName")
    if map_code not in MAP_NAMES:
        return None, map_code, 0

    telemetry_url = next(
        i["attributes"]["URL"] for i in match.get("included", []) if i.get("type") == "asset"
    )
    events = session.get(telemetry_url, headers={"Accept-Encoding": "gzip"}, timeout=180).json()

    start = None
    for e in events:
        if e.get("_T") == "LogMatchStart":
            start = parse_time(e["_D"])
            break

    rows = []
    for e in events:
        if e.get("_T") != "LogVehicleRide":
            continue
        character = e.get("character") or {}
        loc = character.get("location") or {}
        vehicle = e.get("vehicle") or {}
        elapsed = ""
        if start and e.get("_D"):
            elapsed = round((parse_time(e["_D"]) - start).total_seconds(), 1)
        rows.append({
            "match_id": match_id,
            "map_name": MAP_NAMES[map_code],
            "map_code": map_code,
            "game_mode": attrs.get("gameMode", ""),
            "match_type": attrs.get("matchType", ""),
            "created_at": attrs.get("createdAt", ""),
            "vehicle_id": vehicle.get("vehicleId", ""),
            "vehicle_type": vehicle.get("vehicleType", ""),
            "seat_index": e.get("seatIndex", ""),
            "x": loc.get("x", ""),
            "y": loc.get("y", ""),
            "z": loc.get("z", ""),
            "elapsed_time": elapsed,
            "is_game": (e.get("common") or {}).get("isGame", ""),
        })
    return rows, map_code, len(events)


def count_rows():
    if not os.path.exists(OUTPUT):
        return 0
    with open(OUTPUT, encoding="utf-8-sig") as f:
        return max(sum(1 for _ in f) - 1, 0)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    key = get_key()

    done = set()
    if os.path.exists(DONE):
        with open(DONE, encoding="utf-8") as f:
            done = {line.strip() for line in f if line.strip()}

    total = count_rows()
    new_file = not os.path.exists(OUTPUT)
    print(f"현재 저장된 기록: {total}건 / 목표: {TARGET_ROWS}건")

    with open(OUTPUT, "a", newline="", encoding="utf-8-sig") as out, open(DONE, "a", encoding="utf-8") as done_file:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        now = datetime.now(timezone.utc)
        for day in range(0, DAYS_BACK + 1):
            if total >= TARGET_ROWS:
                break
            start_time = None if day == 0 else (now - timedelta(days=day)).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"\n[{'최근' if day == 0 else f'{day}일 전'} 샘플 경기 목록 가져오는 중]")
            try:
                match_ids = get_sample_match_ids(key, start_time)
            except Exception as e:
                print(f"  목록을 가져오지 못했습니다: {e}")
                continue
            print(f"  경기 {len(match_ids)}개 발견")

            for match_id in match_ids:
                if total >= TARGET_ROWS:
                    break
                if match_id in done:
                    continue
                try:
                    rows, map_code, event_count = process_match(key, match_id)
                except Exception as e:
                    print(f"  경기 {match_id[:8]} 오류: {e}")
                    continue

                if rows is None:
                    print(f"  다른 맵({map_code}) 건너뜀")
                    continue
                if not rows:
                    print(f"  {MAP_NAMES[map_code]} 경기인데 탑승 기록 0건 (전체 이벤트 {event_count}개)")

                writer.writerows(rows)
                out.flush()
                done_file.write(match_id + "\n")
                done_file.flush()
                done.add(match_id)
                total += len(rows)
                if rows:
                    print(f"  {rows[0]['map_name']} 경기 +{len(rows)}건 → 누적 {total}건")

    print(f"\n수집 완료! 총 {total}건이 {OUTPUT}에 저장되었습니다.")


if __name__ == "__main__":
    main()