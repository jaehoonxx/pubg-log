import streamlit as st
from db import init_db, get_map_info
from PIL import Image
import folium
import folium.raster_layers
from folium.plugins import HeatMap
from branca.element import MacroElement
from jinja2 import Template
from streamlit_folium import st_folium
import os
import base64
from io import BytesIO
import html
import math
import pandas as pd

st.set_page_config(page_title="배그 고정 지형 지도 도감", page_icon="🗺️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

html {
    font-size: 14px;
}

.stApp {
    background:
        linear-gradient(rgba(242,169,0,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(242,169,0,0.04) 1px, transparent 1px),
        radial-gradient(circle at 20% 0%, #2e3a24 0%, transparent 50%),
        radial-gradient(circle at 100% 100%, #3a2a12 0%, transparent 45%),
        #121410;
    background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%, 100% 100%;
    background-attachment: fixed;
    color: #e8e6df;
    font-family: 'Noto Sans KR', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

h1 {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 900 !important;
    color: #ffc226 !important;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    border-left: 6px solid #f2a900;
    padding-left: 16px !important;
}

h2, h3, h4, h5 {
    color: #f5f3ea !important;
}

[data-testid="stCaptionContainer"], .stCaption, small {
    color: #d6d3c4 !important;
    font-size: 0.95rem !important;
}

hr {
    border-color: rgba(242,169,0,0.3) !important;
}

.stButton > button, [data-testid="stPopover"] button {
    background: #1e221a;
    color: #f5f3ea;
    border: 1px solid #f2a900;
    border-radius: 6px;
    font-weight: 700;
    transition: all 0.2s;
}

.stButton > button:hover, [data-testid="stPopover"] button:hover {
    background: #f2a900;
    color: #121410;
    border-color: #f2a900;
}

[data-testid="stAlert"] {
    background: rgba(30,34,26,0.85) !important;
    border: 1px solid rgba(242,169,0,0.4);
    border-radius: 8px;
    color: #e8e6df !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] li,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: #f0ede2 !important;
    line-height: 1.7;
}

[data-testid="stAlert"] strong {
    color: #ffc226 !important;
}

.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: #f2a900 !important;
    color: #121410 !important;
    border: 1px solid #f2a900 !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(30,34,26,0.92);
    border-color: rgba(242,169,0,0.5) !important;
    border-radius: 10px;
}

[data-testid="stColumn"], [data-testid="column"] {
    position: relative;
}

.stat-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin: 18px 0 6px;
}

.stat-card {
    background: rgba(30,34,26,0.85);
    border: 1px solid rgba(242,169,0,0.35);
    border-top: 3px solid #f2a900;
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: transform 0.2s, border-color 0.2s;
}

.stat-card.active {
    background: rgba(242,169,0,0.14);
    border-color: #f2a900;
    box-shadow: 0 0 0 1px #f2a900, 0 6px 20px rgba(242,169,0,0.18);
}

[class*="st-key-card_"] button {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 14px;
    min-height: 66px !important;
    margin-top: 8px;
    padding: 10px 14px !important;
    background: rgba(30,34,26,0.85) !important;
    border: 1px solid rgba(242,169,0,0.35) !important;
    border-top: 3px solid #f2a900 !important;
    border-radius: 10px !important;
    text-align: left !important;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s !important;
}

[class*="st-key-card_"][class*="_on"] button {
    background: rgba(242,169,0,0.14) !important;
    border-color: #f2a900 !important;
    box-shadow: 0 0 0 1px #f2a900, 0 6px 20px rgba(242,169,0,0.18);
}

[class*="st-key-card_"] button:hover {
    background: rgba(30,34,26,0.95) !important;
    border-color: #f2a900 !important;
    transform: translateY(-3px);
}

[class*="st-key-card_"][class*="_on"] button:hover {
    background: rgba(242,169,0,0.18) !important;
}

[class*="st-key-card_"] button::before {
    font-size: 1.9rem;
    line-height: 1;
}

[class*="st-key-card_vehicle"] button, [class*="st-key-card_secret"] button {
    min-height: 96px !important;
}

[class*="st-key-card_vehicle"] button::before {
    content: "🚗";
}

[class*="st-key-card_secret"] button::before {
    content: "🔑";
}

[class*="st-key-card_map"] button::before {
    content: "🗺️";
}

[class*="st-key-card_map"] button strong {
    font-size: 1.35rem;
}

[class*="st-key-card_"] button > div {
    justify-content: flex-start !important;
    width: auto !important;
}

[class*="st-key-card_"] button p {
    display: grid !important;
    grid-template-columns: auto 1fr;
    align-items: end;
    column-gap: 2px;
    margin: 0 !important;
    text-align: left !important;
}

[class*="st-key-card_"] button strong {
    grid-column: 1;
    grid-row: 1;
    font-size: 1.7rem;
    font-weight: 900;
    color: #ffc226 !important;
    line-height: 1.1;
}

[class*="st-key-card_"] button code {
    grid-column: 2;
    grid-row: 1;
    background: none !important;
    padding: 0 !important;
    margin-bottom: 3px;
    font-family: inherit !important;
    font-size: 0.95rem !important;
    font-weight: 700;
    color: #f0ede2 !important;
}

[class*="st-key-card_"] button em {
    grid-column: 1 / span 2;
    grid-row: 2;
    font-style: normal;
    font-size: 0.85rem;
    color: #bdb9a8 !important;
    margin-top: 2px;
}

.stat-card:hover {
    transform: translateY(-3px);
    border-color: #f2a900;
}

.stat-icon {
    font-size: 1.9rem;
    line-height: 1;
}

.stat-num {
    font-size: 1.7rem;
    font-weight: 900;
    color: #ffc226;
    line-height: 1.1;
}

.stat-num small {
    font-size: 0.95rem;
    font-weight: 700;
    color: #f0ede2;
    margin-left: 2px;
}

.stat-label {
    font-size: 0.85rem;
    color: #bdb9a8;
    margin-top: 2px;
}

@media (max-width: 800px) {
    .stat-row {
        grid-template-columns: 1fr;
    }
}

.info-card {
    background: rgba(30,34,26,0.85);
    border: 1px solid rgba(242,169,0,0.35);
    border-top: 3px solid #f2a900;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 8px;
}

.info-title {
    color: #ffc226;
    font-weight: 900;
    font-size: 1.1rem;
    margin-bottom: 10px;
}

.info-highlight {
    background: rgba(242,169,0,0.12);
    border-left: 3px solid #f2a900;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 10px;
    color: #f0ede2;
    font-size: 0.92rem;
    line-height: 1.5;
}

.info-verdict {
    color: #ffc226;
    font-weight: 900;
    font-size: 1rem;
    margin-bottom: 6px;
}

.info-compare {
    color: #bdb9a8;
    font-size: 0.82rem;
    margin-top: 2px;
}

.info-highlight b {
    color: #ffc226;
    font-size: 1.35rem;
}

.info-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px dashed rgba(242,169,0,0.18);
    font-size: 0.92rem;
}

.info-row span:first-child {
    color: #bdb9a8;
}

.info-row span:last-child {
    color: #f0ede2;
    font-weight: 700;
}

.info-sub {
    color: #ffc226;
    font-weight: 700;
    font-size: 0.88rem;
    margin: 12px 0 6px;
}

.vbar {
    display: grid;
    grid-template-columns: 118px 1fr 38px;
    align-items: center;
    gap: 8px;
    margin: 4px 0;
    font-size: 0.82rem;
}

.vbar-name {
    color: #e8e6df;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.vbar-track {
    background: rgba(255,255,255,0.07);
    border-radius: 4px;
    height: 10px;
    overflow: hidden;
}

.vbar-fill {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, #b37d00, #ffc226);
    border-radius: 4px;
}

.vbar-num {
    color: #bdb9a8;
    text-align: right;
}

.footer {
    margin-top: 40px;
    padding: 18px 0 6px;
    border-top: 1px solid rgba(242,169,0,0.25);
    text-align: center;
    color: #8f8b7c;
    font-size: 0.82rem;
    line-height: 1.8;
}

.footer b {
    color: #ffc226;
}

.info-note {
    color: #ffb74d;
    font-size: 0.8rem;
    margin-top: 8px;
}

.info-source {
    color: #8f8b7c;
    font-size: 0.78rem;
    margin-top: 10px;
}

.desc-box {
    background: rgba(30,34,26,0.85);
    border: 1px solid rgba(242,169,0,0.4);
    border-radius: 10px;
    padding: 20px 22px;
}

.desc-title {
    color: #ffc226;
    font-weight: 700;
    font-size: 1.02rem;
    border-left: 3px solid #f2a900;
    padding-left: 12px;
    margin: 0 0 10px 4px;
}

.desc-box ul {
    margin: 0 0 22px 0;
    padding-left: 34px;
}

.desc-box ul:last-child {
    margin-bottom: 0;
}

.desc-box li {
    color: #f0ede2;
    line-height: 1.75;
    margin-bottom: 6px;
}

iframe {
    border: 2px solid rgba(242,169,0,0.5) !important;
    border-radius: 10px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.6);
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def setup_db():
    init_db()
    return True


setup_db()


class FitImageBounds(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            var bounds = {{ this.bounds }};
            map.getContainer().style.background = "#161912";
            var imgH = bounds[1][0] - bounds[0][0];
            var imgW = bounds[1][1] - bounds[0][1];
            function fit() {
                map.invalidateSize();
                var size = map.getSize();
                if (!size.x || !size.y) { return; }
                var z = Math.log2(Math.min((size.x - 8) / imgW, (size.y - 8) / imgH));
                map.options.zoomSnap = 0;
                map.setMinZoom(z);
                map.setView([0, 0], z, {animate: false});
            }
            setTimeout(fit, 150);
            setTimeout(fit, 600);
            window.addEventListener("resize", function () { setTimeout(fit, 150); });
        })();
        {% endmacro %}
    """)

    def __init__(self, bounds):
        super().__init__()
        self._name = "FitImageBounds"
        self.bounds = bounds


@st.cache_data
def load_image_as_data_url(path, max_side=4096):
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    width, height = img.size
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=93, optimize=True, subsampling=0)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}", width, height


st.title("🗺️ 배그로그 (PUBG Log) - 고정 지형 정보 도감")
st.caption("맵과 카테고리를 선택하면 맞춤 지도를 한눈에 확인할 수 있습니다.")

MAPS = ["에란겔", "태이고", "론도", "미라마"]
CATS = ["고정 차량", "비밀의 방"]


SPOT_COUNTS = {
    "에란겔": {"고정 차량": 40, "비밀의 방": 15},
    "태이고": {"고정 차량": 25, "비밀의 방": 14},
    "론도": {"고정 차량": 19, "비밀의 방": 15},
    "미라마": {"고정 차량": 41, "비밀의 방": 15},
}

defaults = {
    "selected_map": "에란겔",
    "selected_cat": "고정 차량",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

current_map = st.session_state.selected_map
vehicle_spots = SPOT_COUNTS[current_map]["고정 차량"]
secret_spots = SPOT_COUNTS[current_map]["비밀의 방"]



def select_category(cat):
    st.session_state.selected_cat = cat


def select_map(map_name):
    st.session_state.selected_map = map_name


def stat_card(col, key, icon, num, label, cat):
    state = "on" if st.session_state.selected_cat == cat else "off"
    with col:
        st.button(
            f"**{num}**`개` *{label}*",
            key=f"card_{key}_{state}",
            on_click=select_category,
            args=(cat,),
            use_container_width=True,
        )


MAP_THUMBS = {"에란겔": "images/1.png", "태이고": "images/2.png", "론도": "images/3.png", "미라마": "images/4.png"}


@st.cache_data
def thumb_data_url(path, width=520):
    img = Image.open(path).convert("RGB")
    ratio = width / img.width
    img = img.resize((width, int(img.height * ratio)))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


thumb_css = []
for i, map_name in enumerate(MAPS):
    path = MAP_THUMBS.get(map_name)
    if not path or not os.path.exists(path):
        continue
    url = thumb_data_url(path)
    sel = f'[class*="st-key-card_map{i}_"]'
    thumb_css.append(f"""
{sel} button, {sel} button:hover, {sel}[class*="_on"] button, {sel}[class*="_on"] button:hover {{
    background:
        linear-gradient(90deg, rgba(18,20,16,0.95) 0%, rgba(18,20,16,0.75) 45%, rgba(18,20,16,0.25) 100%),
        url("{url}") center / cover no-repeat !important;
}}
{sel}[class*="_on"] button, {sel}[class*="_on"] button:hover {{
    background:
        linear-gradient(90deg, rgba(60,45,5,0.95) 0%, rgba(60,45,5,0.7) 45%, rgba(242,169,0,0.15) 100%),
        url("{url}") center / cover no-repeat !important;
}}""")
if thumb_css:
    st.markdown("<style>" + "".join(thumb_css) + """
[class*="st-key-card_map"] button::before { content: none !important; }
[class*="st-key-card_map"] button strong { font-size: 1.45rem !important; text-shadow: 0 2px 6px rgba(0,0,0,0.8); }
</style>""", unsafe_allow_html=True)

left_col, right_col, info_col = st.columns([2, 2, 2], gap="medium")

with left_col:
    for i, map_name in enumerate(MAPS):
        state = "on" if st.session_state.selected_map == map_name else "off"
        st.button(
            f"**{map_name}**",
            key=f"card_map{i}_{state}",
            on_click=select_map,
            args=(map_name,),
            use_container_width=True,
        )

stat_card(right_col, "vehicle", "🚗", vehicle_spots, "고정 차량 거점", "고정 차량")
stat_card(right_col, "secret", "🔑", secret_spots, "비밀의 방 위치", "비밀의 방")

VEHICLE_KO = {
    "Uaz": "UAZ", "Dacia": "다시아", "PickupTruck": "픽업트럭", "Mirado": "미라도",
    "MiradoOpen": "미라도 오픈카", "PonyCoupe": "포니 쿠페", "Pony": "포니", "Motorbike": "오토바이",
    "CoupeRB": "쿠페 RB", "Buggy": "버기", "BRDM": "BRDM", "EmergencyPickupVehicle": "긴급 픽업",
    "Rony": "로니", "Mini": "미니", "Scooter": "스쿠터", "Tukshai": "툭샤이", "Dirtbike": "더트바이크",
    "Blanc": "블랑", "Porter": "포터", "Motorglider": "모터 글라이더", "Boat": "보트",
    "AquaRail": "아쿠아레일", "Snowmobile": "스노모빌", "Zima": "지마", "Bicycle": "자전거",
    "MountainBike": "산악자전거", "Van": "밴", "PicoBus": "피코버스",
}
SKIN_BASE = {
    "FlyingSpur": "Dacia",
    "ContinentalGTC": "CoupeRB",
    "DBX": "Uaz",
    "Cayenne": "Uaz",
}
SKIN_SUFFIX = ("_LGD", "_ULT", "_EP", "_SE", "_PRM", "_EPIC", "_ESPORTS")


VEHICLE_KO_LOWER = {k.lower(): v for k, v in VEHICLE_KO.items()}
SKIN_BASE_LOWER = {k.lower(): v.lower() for k, v in SKIN_BASE.items()}


def vehicle_ko(name):
    key = str(name).lower()
    is_skin = False
    for suffix in SKIN_SUFFIX:
        if key.endswith(suffix.lower()):
            key = key[: -len(suffix)]
            is_skin = True
            break
    key = SKIN_BASE_LOWER.get(key, key)
    if key in VEHICLE_KO_LOWER:
        return VEHICLE_KO_LOWER[key]
    return "기타 스킨 차량" if is_skin else str(name)



@st.cache_data
def load_analysis(path=None):
    if path is None:
        candidates = ["label/app_rides.csv", "label/labeled_rides.csv"]
        path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None or not os.path.exists(path):
        return None
    cols = ["map_name", "match_id", "vehicle", "elapsed_time", "nearest_dist_m", "created_at", "x", "y"]
    return pd.read_csv(path, encoding="utf-8-sig", usecols=cols)


def render_analysis(map_name, early_min=5, radius_m=100):
    data = load_analysis()
    if data is None:
        st.info("분석 데이터(label/app_rides.csv)가 없어 요약을 표시할 수 없어요.")
        return

    sub = data[data["map_name"] == map_name]
    early = sub[sub["elapsed_time"] <= early_min * 60]
    late = sub[sub["elapsed_time"] > early_min * 60]
    p_early = (early["nearest_dist_m"] <= radius_m).mean() * 100 if len(early) else 0
    p_late = (late["nearest_dist_m"] <= radius_m).mean() * 100 if len(late) else 0
    ratio = p_early / p_late if p_late else 0

    top = sub["vehicle"].map(vehicle_ko).value_counts()
    top5 = top.head(5)
    bars = ""
    for name, cnt in top5.items():
        width = cnt / top5.iloc[0] * 100
        label = html.escape(name)
        bars += (
            f'<div class="vbar"><span class="vbar-name">{label}</span>'
            f'<span class="vbar-track"><span class="vbar-fill" style="width:{width:.0f}%"></span></span>'
            f'<span class="vbar-num">{cnt / len(sub) * 100:.0f}%</span></div>'
        )

    dates = pd.to_datetime(data["created_at"], errors="coerce").dropna()
    period = f"{dates.min():%Y.%m.%d} ~ {dates.max():%Y.%m.%d}" if len(dates) else "-"
    n_matches = data["match_id"].nunique()

    if len(early) < 100:
        verdict = "📍 아직 데이터가 부족해 확인 중이에요"
    elif ratio >= 1.3:
        verdict = "📍 이 지도의 고정 차량 위치, 실제 경기에서도 맞았어요"
    else:
        verdict = "📍 고정 차량 자리와 다른 곳의 차이가 아직 뚜렷하지 않아요"
    headline = (
        f'<div class="info-verdict">{verdict}</div>'
        f'경기 초반에 차를 탄 100명 중 <b>{p_early:.0f}명</b>이 고정 차량 자리에서 탔어요'
        f'<div class="info-compare">(5분 이후엔 100명 중 {p_late:.0f}명)</div>'
    )

    note = ""
    if len(early) < 100:
        note = f'<div class="info-note">⚠️ {map_name} 맵은 초반 탑승 기록이 {len(early)}건뿐이라 참고용으로 봐주세요.</div>'

    card = (
        f'<div class="info-card">'
        f'<div class="info-title">📊 {map_name} 데이터 분석</div>'
        f'<div class="info-highlight">{headline}</div>'
        f'<div class="info-row"><span>분석한 탑승 기록</span><span>{len(sub):,}건</span></div>'
        f'<div class="info-row"><span>초반 {early_min}분 · {radius_m}m 이내 비율</span><span>{p_early:.1f}%</span></div>'
        f'<div class="info-row"><span>{early_min}분 이후 · {radius_m}m 이내 비율</span><span>{p_late:.1f}%</span></div>'
        f'<div class="info-sub">🚙 많이 탄 차량 TOP 5</div>'
        f'{bars}'
        f'{note}'
        f'<div class="info-source">PUBG 공식 API · {n_matches}경기 분석 · {period}</div>'
        f'</div>'
    )
    st.markdown(card, unsafe_allow_html=True)


with info_col:
    render_analysis(st.session_state.selected_map)
st.markdown("---")



def render_description(text):
    parts = []
    items = []

    def flush():
        if items:
            parts.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("•"):
            flush()
            title = line.lstrip("•").strip().lstrip("-").strip()
            parts.append(f'<div class="desc-title">{html.escape(title)}</div>')
        else:
            items.append(html.escape(line.lstrip("-").strip()))
    flush()
    return '<div class="desc-box">' + "".join(parts) + "</div>"


selected_map = st.session_state.selected_map
selected_cat = st.session_state.selected_cat

map_info = get_map_info(selected_map, selected_cat)

if map_info:
    map_image_path, description = map_info

    icon = "🚗" if selected_cat == "고정 차량" else "🔑"
    st.subheader(f"{icon} {selected_map} - {selected_cat} 위치 지도")

    col_map, col_txt = st.columns([1.15, 1])

    with col_map:
        abs_path = os.path.abspath(map_image_path)

        show_heat, early_only = False, False
        heat_available = selected_cat == "고정 차량" and load_analysis() is not None
        if heat_available:
            t1, t2, _ = st.columns([1.3, 1.3, 2])
            show_heat = t1.toggle("🔥 실제 탑승 히트맵", value=st.session_state.get("heat_saved", False))
            early_only = t2.toggle("⏱️ 초반 5분만", value=st.session_state.get("early_saved", True), disabled=not show_heat)
            st.session_state.heat_saved = show_heat
            st.session_state.early_saved = early_only

        if os.path.exists(abs_path):
            try:
                data_url, width, height = load_image_as_data_url(abs_path)

                half_h, half_w = height / 2, width / 2
                bounds = [[-half_h, -half_w], [half_h, half_w]]

                MAP_HEIGHT = 620
                fit_zoom = min(math.log2((MAP_HEIGHT - 20) / height), math.log2(880 / width))
                fit_zoom = math.floor(fit_zoom * 4) / 4

                m = folium.Map(
                    location=[0, 0],
                    crs="Simple",
                    tiles=None,
                    zoom_start=fit_zoom,
                    min_zoom=-6,
                    max_zoom=0.5,
                    zoom_snap=0.25,
                    zoom_delta=0.5,
                    max_bounds=True,
                    min_lat=-half_h,
                    max_lat=half_h,
                    min_lon=-half_w,
                    max_lon=half_w,
                    attributionControl=False,
                )

                folium.raster_layers.ImageOverlay(
                    image=data_url,
                    bounds=bounds,
                    opacity=1.0,
                ).add_to(m)

                pts = []
                if heat_available:
                    rides = load_analysis()
                    rides = rides[rides["map_name"] == selected_map]
                    if early_only:
                        rides = rides[rides["elapsed_time"] <= 300]
                if show_heat:
                    pts = [
                        [half_h - y / 816000 * height, x / 816000 * width - half_w]
                        for x, y in zip(rides["x"], rides["y"])
                    ]
                    if pts:
                        HeatMap(pts, radius=14, blur=18, min_opacity=0.35).add_to(m)

                FitImageBounds(bounds).add_to(m)

                st_folium(
                    m,
                    height=MAP_HEIGHT,
                    returned_objects=[],
                    use_container_width=True,
                    key=f"map_{selected_map}_{selected_cat}_{show_heat}_{early_only}",
                )
                if heat_available:
                    scope = "경기 초반 5분" if early_only else "경기 전체"
                    if show_heat:
                        st.caption(f"🔥 PUBG 공식 API로 수집한 실제 탑승 위치 {len(rides):,}건 ({scope}) · 빨갛게 진할수록 많이 탄 곳이에요.")
                    else:
                        st.caption(f"🔥 위의 「실제 탑승 히트맵」을 켜면 PUBG 공식 API로 수집한 실제 탑승 위치 {len(rides):,}건 ({scope})을 지도 위에서 볼 수 있어요.")
                st.caption("💡 지도 위에서 **마우스 휠**을 굴리면 확대할 수 있고, 드래그하여 이동할 수 있습니다.")
            except Exception as e:
                st.error(f"이미지 처리 중 오류 발생: {e}")
        else:
            st.error(f"이미지 파일을 찾을 수 없습니다. 경로를 확인해 주세요: {abs_path}")

    with col_txt:
        st.markdown(f"### {icon} {selected_cat} 상세 안내")
        st.markdown(render_description(description), unsafe_allow_html=True)

        st.markdown("---")
        if selected_cat == "고정 차량":
            st.success("💡 **Tip**: 게임 대기 시간에 지도 위치를 확인하고 낙하 지점을 미리 결정하세요.")
        else:
            st.warning("💡 **Tip**: 맵에 따라 열쇠나 카드키가 필요할 수 있으니, 인게임에서 먼저 확보한 뒤 이동하세요.")
else:
    st.error("선택한 조건의 지도 데이터를 찾을 수 없습니다.")

st.markdown("""
<div class="footer">
<b>🗺️ 배그로그 (PUBG Log)</b> · 고정 지형 정보 도감<br>
데이터 출처: PUBG 공식 API · 지도 이미지 출처는 각 이미지 표기 참고<br>
본 사이트는 KRAFTON 및 PUBG와 무관한 학생 팬 프로젝트입니다.
</div>
""", unsafe_allow_html=True)