import os
from collections import deque

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter, ImageDraw

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

CLEAN = "data/vehicle_rides_clean.csv"
OUT_DIR = "label"
REVIEW_DIR = os.path.join(OUT_DIR, "review")
MAP_SIZE = 816000
MAPS = ["에란겔", "태이고", "론도", "미라마"]
MAP_IMAGES = {"에란겔": "images/1.png", "태이고": "images/2.png", "론도": "images/3.png", "미라마": "images/4.png"}
SPOT_COUNTS = {"에란겔": 40, "태이고": 25, "론도": 19, "미라마": 41}

EARLY_MIN = 5
RADIUS_M = 50
REVIEW_N = 100


def color_mask(arr, kind):
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    if kind == "magenta":
        return (r > 170) & (b > 170) & (g < 100)
    return (r > 200) & (g > 170) & (b < 90)


def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    found = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        ys, xs = [], []
        while q:
            y, x = q.popleft()
            ys.append(y)
            xs.append(x)
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        found.append({
            "px": (min(xs) + max(xs)) / 2,
            "py": (min(ys) + max(ys)) / 2,
            "size": max(max(xs) - min(xs), max(ys) - min(ys)) + 1,
        })
    return found


def find_markers(img):
    arr = np.asarray(img.convert("RGB")).astype(int)
    result = {}
    for kind in ("magenta", "yellow"):
        mask = Image.fromarray((color_mask(arr, kind) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
        result[kind] = components(np.asarray(mask) > 0)

    sizes = [c["size"] for c in result["magenta"] if c["size"] >= 8]
    ref = float(np.median(sizes)) if sizes else 20.0

    markers = []
    for kind, comps in result.items():
        for c in comps:
            if 0.5 * ref <= c["size"] <= 1.6 * ref:
                markers.append({"type": "고정차" if kind == "magenta" else "차고", "px": c["px"], "py": c["py"]})
    return markers


def detect_all():
    rows = []
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    for ax, map_name in zip(axes.flat, MAPS):
        img = Image.open(MAP_IMAGES[map_name])
        w, h = img.size
        markers = find_markers(img)
        for m in markers:
            m.update({
                "map_name": map_name,
                "x": m["px"] / w * MAP_SIZE,
                "y": m["py"] / h * MAP_SIZE,
            })
            rows.append(m)

        n_fixed = sum(1 for m in markers if m["type"] == "고정차")
        n_garage = len(markers) - n_fixed
        print(f"  {map_name}: 고정차 {n_fixed}개 + 차고 {n_garage}개 = {len(markers)}개 (직접 센 숫자: {SPOT_COUNTS[map_name]}개)")

        ax.imshow(img)
        for m in markers:
            color = "#00e5ff" if m["type"] == "고정차" else "#00ff66"
            ax.add_patch(plt.Circle((m["px"], m["py"]), radius=w * 0.018, fill=False, color=color, lw=2))
        ax.set_title(f"{map_name} 찾은 아이콘 {len(markers)}개")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "markers_check.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  확인용 이미지 저장: {path}")

    markers = pd.DataFrame(rows)[["map_name", "type", "px", "py", "x", "y"]]
    markers.to_csv(os.path.join(OUT_DIR, "markers.csv"), index=False, encoding="utf-8-sig")
    return markers


def add_distance(df, markers):
    df = df.copy()
    df["nearest_dist_m"] = np.nan
    df["nearest_type"] = ""
    for map_name in MAPS:
        idx = df.index[df["map_name"] == map_name]
        mk = markers[markers["map_name"] == map_name]
        if len(idx) == 0 or len(mk) == 0:
            continue
        rides = df.loc[idx, ["x", "y"]].to_numpy()
        pts = mk[["x", "y"]].to_numpy()
        d = np.sqrt(((rides[:, None, :] - pts[None, :, :]) ** 2).sum(axis=2)) / 100
        nearest = d.argmin(axis=1)
        df.loc[idx, "nearest_dist_m"] = d[np.arange(len(idx)), nearest].round(1)
        df.loc[idx, "nearest_type"] = mk["type"].to_numpy()[nearest]
    return df


def distance_report(df):
    early = df[df["elapsed_min"] <= EARLY_MIN]
    late = df[df["elapsed_min"] > EARLY_MIN]
    print(f"\n=== 가장 가까운 고정 위치까지 거리 (초반 {EARLY_MIN}분 vs 이후) ===")
    for r in (25, 50, 100, 200):
        print(f"  {r}m 이내: 초반 {(early['nearest_dist_m'] <= r).mean() * 100:5.1f}%   이후 {(late['nearest_dist_m'] <= r).mean() * 100:5.1f}%")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = np.arange(0, 505, 10)
    ax.hist(late["nearest_dist_m"].clip(upper=500), bins=bins, density=True, alpha=0.6, color="#888", label=f"{EARLY_MIN}분 이후")
    ax.hist(early["nearest_dist_m"].clip(upper=500), bins=bins, density=True, alpha=0.7, color="#f2a900", label=f"초반 {EARLY_MIN}분")
    ax.axvline(RADIUS_M, color="red", ls="--", label=f"라벨 기준 {RADIUS_M}m")
    ax.set_title("탑승 위치에서 가장 가까운 고정 위치까지 거리")
    ax.set_xlabel("거리 (m, 500m 이상은 500에 포함)")
    ax.set_ylabel("비율")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "distance_hist.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  그래프 저장: {path}")


def make_review(df):
    os.makedirs(REVIEW_DIR, exist_ok=True)
    border = df[(df["elapsed_min"] <= EARLY_MIN) & (df["nearest_dist_m"].between(RADIUS_M * 0.5, RADIUS_M * 2))]
    sample = border.sample(min(REVIEW_N, len(border)), random_state=42).copy()
    sample.insert(0, "review_id", range(1, len(sample) + 1))
    sample["manual_label"] = ""

    images = {m: Image.open(MAP_IMAGES[m]).convert("RGB") for m in MAPS}
    tiles = []
    for _, row in sample.iterrows():
        img = images[row["map_name"]]
        w, h = img.size
        cx, cy = row["x"] / MAP_SIZE * w, row["y"] / MAP_SIZE * h
        half = 250 * 100 / MAP_SIZE * w
        box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
        tile = img.crop(box).resize((260, 260))
        d = ImageDraw.Draw(tile)
        rr = RADIUS_M * 100 / MAP_SIZE * w * (260 / (2 * half))
        d.ellipse((130 - rr, 130 - rr, 130 + rr, 130 + rr), outline=(255, 0, 0), width=2)
        d.ellipse((124, 124, 136, 136), fill=(0, 229, 255), outline=(0, 0, 0))
        d.rectangle((0, 0, 70, 22), fill=(0, 0, 0))
        d.text((5, 4), f"#{row['review_id']}", fill=(255, 255, 255))
        tiles.append(tile)

    per_sheet = 20
    for s in range(0, len(tiles), per_sheet):
        sheet = Image.new("RGB", (5 * 260, 4 * 260), (30, 30, 30))
        for i, t in enumerate(tiles[s:s + per_sheet]):
            sheet.paste(t, ((i % 5) * 260, (i // 5) * 260))
        sheet.save(os.path.join(REVIEW_DIR, f"review_{s // per_sheet + 1:02d}.png"))

    path = os.path.join(OUT_DIR, "review_sample.csv")
    sample.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\n=== 수작업 검수용 샘플 {len(sample)}건 ===")
    print(f"  검수 이미지: {REVIEW_DIR} 폴더")
    print(f"  검수 표: {path} (manual_label 칸에 1 또는 0 입력)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== 1. 지도 이미지에서 고정 위치 아이콘 찾기 ===")
    markers = detect_all()

    print("\n=== 2. 탑승 기록마다 가장 가까운 고정 위치까지 거리 계산 ===")
    df = pd.read_csv(CLEAN, encoding="utf-8-sig")
    df["elapsed_min"] = df["elapsed_time"] / 60
    df = add_distance(df, markers)
    distance_report(df)

    print(f"\n=== 3. 자동 1차 라벨링 (초반 {EARLY_MIN}분 이내 + {RADIUS_M}m 이내 → 1) ===")
    df["auto_label"] = ((df["elapsed_min"] <= EARLY_MIN) & (df["nearest_dist_m"] <= RADIUS_M)).astype(int)
    counts = df["auto_label"].value_counts().reindex([1, 0], fill_value=0)
    print(f"  1 (고정 스폰): {counts[1]}건")
    print(f"  0 (랜덤 스폰): {counts[0]}건")
    print("\n  맵별 라벨 1 건수:")
    print(df[df["auto_label"] == 1]["map_name"].value_counts().reindex(MAPS, fill_value=0).to_string())

    path = os.path.join(OUT_DIR, "labeled_rides.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  저장: {path}")

    make_review(df)
    print("\n라벨링 1단계 완료!")


if __name__ == "__main__":
    main()