import os
import re

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

RAW = "data/vehicle_rides.csv"
CLEAN = "data/vehicle_rides_clean.csv"
OUT_DIR = "eda"
MAP_SIZE = 816000
MAPS = ["에란겔", "태이고", "론도", "미라마"]
MAP_IMAGES = {"에란겔": "images/1.png", "태이고": "images/2.png", "론도": "images/3.png", "미라마": "images/4.png"}


def vehicle_name(vehicle_id):
    if not isinstance(vehicle_id, str) or not vehicle_id:
        return "Unknown"
    parts = vehicle_id.replace("BP_", "").split("_")
    name = []
    for p in parts:
        if p == "C" or re.fullmatch(r"[A-Z]", p) or re.search(r"\d", p) or p.lower().startswith("v"):
            break
        name.append(p)
    return "_".join(name) if name else parts[0]


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  그래프 저장: {path}")


def preprocess(df):
    steps = [("원본 수집", len(df))]

    df = df[df["map_name"].isin(MAPS)]
    steps.append(("맵 필터링 (4개 맵만)", len(df)))

    df = df.dropna(subset=["x", "y", "elapsed_time"])
    steps.append(("결측치 제거 (좌표·시간 없음)", len(df)))

    df = df[~df["vehicle_id"].astype(str).str.contains("Aircraft")]
    steps.append(("비행기 제거 (수송기·재투입기)", len(df)))

    df = df[df["is_game"] > 0.1]
    steps.append(("대기실·비행 단계 제거 (isGame ≤ 0.1)", len(df)))

    df = df[(df["x"] > 0) & (df["x"] < MAP_SIZE) & (df["y"] > 0) & (df["y"] < MAP_SIZE) & (df["elapsed_time"] >= 0)]
    steps.append(("좌표 이상치 제거 (플레이 영역 밖·음수 시간)", len(df)))

    df = df.drop_duplicates(subset=["match_id", "vehicle_id", "seat_index", "x", "y", "elapsed_time"])
    steps.append(("중복 제거", len(df)))

    return df.copy(), steps


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raw = pd.read_csv(RAW, encoding="utf-8-sig")

    print("=== 원본 데이터 기본 정보 ===")
    print(f"행 수: {len(raw)} / 열 수: {raw.shape[1]}")
    print(f"경기 수: {raw['match_id'].nunique()}")
    print("\n열별 결측치 수:")
    print(raw.isna().sum().to_string())

    print("\n=== 게임 모드별 건수 ===")
    print(raw["game_mode"].value_counts().to_string())

    out_mask = (
        (raw["x"] <= 0) | (raw["x"] >= MAP_SIZE) | (raw["y"] <= 0) | (raw["y"] >= MAP_SIZE) | (raw["elapsed_time"] < 0)
    )
    print(f"\n=== 이상치 상세 ({out_mask.sum()}건) ===")
    print("이상치 비율:", f"{out_mask.mean() * 100:.1f}%")
    print("\n이상치의 게임 모드:")
    print(raw.loc[out_mask, "game_mode"].value_counts().to_string())
    print("\n이상치의 isGame 값:")
    print(raw.loc[out_mask, "is_game"].value_counts().head(10).to_string())
    print("\n이상치의 차량 종류 상위 5개:")
    print(raw.loc[out_mask, "vehicle_id"].apply(vehicle_name).value_counts().head(5).to_string())

    df, steps = preprocess(raw)
    df["vehicle"] = df["vehicle_id"].apply(vehicle_name)
    df["elapsed_min"] = df["elapsed_time"] / 60
    df.to_csv(CLEAN, index=False, encoding="utf-8-sig")

    print("\n=== 전처리 단계별 남은 건수 ===")
    for name, n in steps:
        print(f"{name}: {n}건")
    print(f"→ 저장: {CLEAN}")

    print("\n=== 맵별 건수 ===")
    map_counts = df["map_name"].value_counts().reindex(MAPS, fill_value=0)
    print(map_counts.to_string())

    print("\n=== 차량 종류 상위 10개 ===")
    vehicle_counts = df["vehicle"].value_counts()
    print(vehicle_counts.head(10).to_string())

    print("\n=== 탑승 시간 (분) ===")
    print(df["elapsed_min"].describe().round(2).to_string())

    driver_ratio = (df["seat_index"] == 0).mean() * 100
    print(f"\n운전석 탑승 비율: {driver_ratio:.1f}%")

    print("\n=== 그래프 만들기 ===")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(map_counts.index, map_counts.values, color="#f2a900")
    ax.bar_label(bars)
    ax.set_title("맵별 차량 탑승 건수")
    ax.set_ylabel("건수")
    save(fig, "1_map_counts.png")

    top = vehicle_counts.head(15)[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top.index, top.values, color="#6b8e23")
    ax.set_title("차량 종류별 탑승 건수 (상위 15)")
    ax.set_xlabel("건수")
    save(fig, "2_vehicle_counts.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["elapsed_min"], bins=60, color="#f2a900", edgecolor="#333")
    ax.set_title("경기 시작 후 탑승 시간 분포")
    ax.set_xlabel("경과 시간 (분)")
    ax.set_ylabel("건수")
    save(fig, "3_elapsed_time.png")

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    for ax, map_name in zip(axes.flat, MAPS):
        sub = df[df["map_name"] == map_name]
        img_path = MAP_IMAGES[map_name]
        if os.path.exists(img_path):
            ax.imshow(Image.open(img_path), extent=[0, MAP_SIZE, MAP_SIZE, 0])
        else:
            ax.set_xlim(0, MAP_SIZE)
            ax.set_ylim(MAP_SIZE, 0)
        if len(sub):
            ax.hexbin(sub["x"], sub["y"], gridsize=70, mincnt=1, bins="log", cmap="hot", alpha=0.65)
        ax.set_title(f"{map_name} 탑승 위치 히트맵 ({len(sub)}건)")
        ax.set_xticks([])
        ax.set_yticks([])
    save(fig, "4_heatmap.png")

    early = df[df["elapsed_min"] <= 5]
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    for ax, map_name in zip(axes.flat, MAPS):
        sub = early[early["map_name"] == map_name]
        img_path = MAP_IMAGES[map_name]
        if os.path.exists(img_path):
            ax.imshow(Image.open(img_path), extent=[0, MAP_SIZE, MAP_SIZE, 0])
        else:
            ax.set_xlim(0, MAP_SIZE)
            ax.set_ylim(MAP_SIZE, 0)
        if len(sub):
            ax.scatter(sub["x"], sub["y"], s=4, c="#00e5ff", alpha=0.5)
        ax.set_title(f"{map_name} 경기 초반 5분 탑승 위치 ({len(sub)}건)")
        ax.set_xticks([])
        ax.set_yticks([])
    save(fig, "5_early_rides.png")

    print("\nEDA 완료! eda 폴더의 그래프를 확인하세요.")


if __name__ == "__main__":
    main()