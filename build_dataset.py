import os

import pandas as pd

LABELED = "label/labeled_rides.csv"
REVIEW = "label/review_sample.csv"
OUTPUT = "data/dataset.csv"
EARLY_MIN = 5
RADIUS_M = 50
CANDIDATES = [25, 50, 75, 100]
REVIEW_N = 100
MIN_TOTAL = 2000
NEG_RATIO = 3
MAPS = ["에란겔", "태이고", "론도", "미라마"]
COLUMNS = [
    "map_name", "vehicle", "vehicle_type", "seat_index", "x", "y",
    "elapsed_time", "nearest_dist_m", "nearest_type", "label", "label_source",
]


def read_csv_any(path):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"{path} 파일을 읽을 수 없습니다.")


def main():
    df = read_csv_any(LABELED)

    border = df[(df["elapsed_min"] <= EARLY_MIN) & (df["nearest_dist_m"].between(RADIUS_M * 0.5, RADIUS_M * 2))]
    sample_idx = border.sample(min(REVIEW_N, len(border)), random_state=42).index
    review_ids = pd.Series(range(1, len(sample_idx) + 1), index=sample_idx)

    review = read_csv_any(REVIEW)
    review["manual_label"] = pd.to_numeric(review["manual_label"], errors="coerce")
    filled = review.dropna(subset=["manual_label"])
    filled = filled[filled["manual_label"].isin([0, 1])]

    df["manual_label"] = pd.NA
    id_to_idx = {rid: idx for idx, rid in review_ids.items()}
    for rid, value in filled.set_index("review_id")["manual_label"].astype(int).items():
        idx = id_to_idx.get(rid)
        if idx is not None:
            df.loc[idx, "manual_label"] = value
    checked = df[df["manual_label"].notna()].copy()
    checked["manual_label"] = checked["manual_label"].astype(int)

    best_r = RADIUS_M
    print(f"=== 1. 수작업 검수 결과 (처음 기준 {RADIUS_M}m) ===")
    if len(checked) == 0:
        print("  manual_label이 입력된 행이 없습니다. 자동 라벨만으로 데이터셋을 만듭니다.")
    else:
        agree = (checked["manual_label"] == checked["auto_label"]).mean() * 100
        auto1_man0 = ((checked["auto_label"] == 1) & (checked["manual_label"] == 0)).sum()
        auto0_man1 = ((checked["auto_label"] == 0) & (checked["manual_label"] == 1)).sum()
        print(f"  검수한 기록: {len(checked)}건")
        print(f"  사람이 1로 판정: {(checked['manual_label'] == 1).sum()}건 / 0으로 판정: {(checked['manual_label'] == 0).sum()}건")
        print(f"  자동 라벨과 일치: {agree:.1f}%")
        print(f"  자동 1 → 검수 후 0으로 수정: {auto1_man0}건")
        print(f"  자동 0 → 검수 후 1로 수정: {auto0_man1}건")

        print("\n=== 2. 기준 거리별 사람 판정과의 일치율 ===")
        best_score = -1
        for r in CANDIDATES:
            rule = (checked["nearest_dist_m"] <= r).astype(int)
            score = (rule == checked["manual_label"]).mean() * 100
            print(f"  {r:>3}m 기준: {score:5.1f}%")
            if score > best_score:
                best_score, best_r = score, r
        print(f"  → 가장 잘 맞는 기준: {best_r}m ({best_score:.1f}%)")

    df["auto_label"] = ((df["elapsed_min"] <= EARLY_MIN) & (df["nearest_dist_m"] <= best_r)).astype(int)
    df["label"] = df["auto_label"]
    df["label_source"] = "auto"
    has_manual = df["manual_label"].notna()
    df.loc[has_manual, "label"] = df.loc[has_manual, "manual_label"].astype(int)
    df.loc[has_manual, "label_source"] = "manual"
    print(f"\n  최종 라벨 기준: 경기 초반 {EARLY_MIN}분 이내 + 고정 위치 {best_r}m 이내 → 1 (검수한 기록은 사람 판정 사용)")

    print("\n=== 3. 전체 라벨 현황 (수정 반영) ===")
    counts = df["label"].value_counts().reindex([1, 0], fill_value=0)
    print(f"  1 (고정 스폰): {counts[1]}건")
    print(f"  0 (랜덤 스폰): {counts[0]}건")

    pos = df[df["label"] == 1]
    neg_pool = df[df["label"] == 0]
    n_neg = min(len(neg_pool), max(len(pos) * NEG_RATIO, MIN_TOTAL - len(pos)))
    neg = neg_pool.sample(n_neg, random_state=42)
    dataset = pd.concat([pos, neg]).sample(frac=1, random_state=42)[COLUMNS]

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    dataset.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print(f"\n=== 4. 학습 데이터셋 ({OUTPUT}) ===")
    print(f"  전체: {len(dataset)}건 {'✅' if len(dataset) >= MIN_TOTAL else '⚠️ 2,000건 미만'}")
    ds_counts = dataset["label"].value_counts().reindex([1, 0], fill_value=0)
    for lab, name in ((1, "고정 스폰"), (0, "랜덤 스폰")):
        print(f"  {lab} ({name}): {ds_counts[lab]}건 ({ds_counts[lab] / len(dataset) * 100:.1f}%)")

    print("\n  맵별 건수:")
    by_map = dataset.groupby(["map_name", "label"]).size().unstack(fill_value=0).reindex(MAPS, fill_value=0)
    by_map.columns = [f"label_{c}" for c in by_map.columns]
    print(by_map.to_string())

    print("\n  라벨 출처:")
    print(dataset["label_source"].value_counts().to_string())

    print("\n데이터셋 구축 완료!")


if __name__ == "__main__":
    main()