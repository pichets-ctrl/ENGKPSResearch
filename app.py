"""
ระบบรายงานวิจัยประจำเดือน — Streamlit Dashboard
รองรับ: File Selector 3 โหมด, Live Update, Auto-detect Date, Summary + Charts
"""
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ระบบรายงานวิจัยประจำเดือน",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS — blinking LIVE badge + Sarabun font
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif; }

.live-badge {
    display: inline-block;
    background: #e53935;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 2px 9px;
    border-radius: 4px;
    animation: blink 1.2s step-start infinite;
    vertical-align: middle;
    margin-left: 10px;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.1; }
}

.header-bar {
    background: linear-gradient(90deg, #1565C0 0%, #283593 100%);
    color: #fff;
    padding: 16px 24px;
    border-radius: 10px;
    margin-bottom: 18px;
}
.header-bar h1 { color: #fff; margin: 0 0 6px 0; font-size: 1.6rem; }
.header-bar small { opacity: .85; font-size: .84rem; line-height: 1.8; }

.metric-card {
    background: #f5f7ff;
    border: 1px solid #d0d9f0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    "last_mtime": None,
    "cached_df": None,
    "cached_key": None,
    "upload_path": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mtime(path: str) -> float | None:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _list_xlsx(folder: str) -> list[str]:
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted(f.name for f in p.glob("*.xlsx"))


def _sheet_names(filepath: str) -> list[str]:
    try:
        return pd.ExcelFile(filepath, engine="openpyxl").sheet_names
    except Exception as exc:
        st.sidebar.error(f"ไม่สามารถเปิดไฟล์: {exc}")
        return []


def _load(filepath: str, sheet: str) -> pd.DataFrame:
    return pd.read_excel(filepath, sheet_name=sheet, engine="openpyxl")


def _fmt(val) -> str:
    if isinstance(val, float):
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _detect_date_cols(df: pd.DataFrame) -> list[str]:
    """Detect columns that are or can be parsed as dates."""
    result = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            result.append(col)
        elif df[col].dtype == object:
            sample = df[col].dropna().head(10)
            try:
                parsed = pd.to_datetime(sample, errors="raise")
                if parsed.notna().all():
                    result.append(col)
            except Exception:
                pass
    return result


# ---------------------------------------------------------------------------
# Sidebar — File Selector
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ การตั้งค่า")
    st.divider()

    tab_path, tab_folder, tab_upload = st.tabs(
        ["📝 ระบุ Path", "📂 สแกน Folder", "⬆️ Upload"]
    )

    chosen_path: str | None = None

    # ---- Tab 1: ระบุ Path โดยตรง ----------------------------------------
    with tab_path:
        direct_path = st.text_input(
            "พิมพ์ Path ไฟล์ .xlsx",
            placeholder=r"C:\Users\...\ข้อมูลเดือนมีนาคม 2569.xlsx",
            key="direct_path",
        )
        if direct_path:
            if Path(direct_path).is_file():
                chosen_path = direct_path
                st.success("✅ พบไฟล์แล้ว")
            else:
                st.error("❌ ไม่พบไฟล์ที่ระบุ")

    # ---- Tab 2: สแกน Folder ----------------------------------------------
    with tab_folder:
        default_folder = str(Path(__file__).parent / "data")
        folder_path = st.text_input(
            "📁 Path โฟลเดอร์",
            value=default_folder,
            key="folder_path",
            help=(
                "ตัวอย่าง Windows:\n"
                r"C:\Users\urfco\OneDrive\Desktop\รองคณบดีผ่ายวิจัย"
                r"\รายงานวิจัยประจำเดือน\รายงานหน่วยวิจัย"
            ),
        )
        xlsx_list = _list_xlsx(folder_path)
        if xlsx_list:
            picked_name = st.selectbox("เลือกไฟล์", xlsx_list, key="sel_file")
            if not chosen_path:
                chosen_path = str(Path(folder_path) / picked_name)
        else:
            st.info("ไม่พบไฟล์ .xlsx ในโฟลเดอร์ที่ระบุ")

    # ---- Tab 3: Upload ---------------------------------------------------
    with tab_upload:
        uploaded = st.file_uploader("อัปโหลดไฟล์ .xlsx", type=["xlsx"])
        if uploaded:
            save_dir = Path(__file__).parent / "data"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / uploaded.name
            save_path.write_bytes(uploaded.getvalue())
            st.session_state.upload_path = str(save_path)
            st.success(f"✅ บันทึก: {uploaded.name}")
        if st.session_state.upload_path and not chosen_path:
            chosen_path = st.session_state.upload_path

    # "ระบุ Path" มีลำดับความสำคัญสูงสุด
    if direct_path and Path(direct_path).is_file():
        chosen_path = direct_path

    st.divider()

    # ---- Sheet selector --------------------------------------------------
    sheet_names: list[str] = []
    selected_sheet: str | None = None
    if chosen_path and Path(chosen_path).is_file():
        sheet_names = _sheet_names(chosen_path)
    if sheet_names:
        selected_sheet = st.selectbox("📋 เลือก Sheet", sheet_names, key="sel_sheet")
    elif chosen_path:
        st.warning("ไม่พบ sheet ในไฟล์นี้")

    st.divider()

    # ---- Live Update controls --------------------------------------------
    st.subheader("🔄 Live Update")
    auto_refresh = st.toggle("เปิด Auto Refresh", value=False)
    refresh_sec = st.slider(
        "อัปเดตทุก (วินาที)", 5, 120, 15, disabled=not auto_refresh
    )

    st.divider()

    # ---- Chart axis selectors (populated after first data load) ----------
    st.subheader("📈 ตั้งค่ากราฟ")
    x_col: str | None = None
    y_cols: list[str] = []

    if chosen_path and selected_sheet and Path(chosen_path).is_file():
        _mt = _mtime(chosen_path)
        _ck = (chosen_path, selected_sheet, _mt)
        if st.session_state.cached_key != _ck:
            st.session_state.cached_df = _load(chosen_path, selected_sheet)
            st.session_state.cached_key = _ck
            if (
                st.session_state.last_mtime is not None
                and _mt != st.session_state.last_mtime
            ):
                st.toast("🔄 ไฟล์มีการเปลี่ยนแปลง — โหลดข้อมูลใหม่แล้ว", icon="✅")
            st.session_state.last_mtime = _mt

        _df_sb = st.session_state.cached_df
        if _df_sb is not None:
            _all = _df_sb.columns.tolist()
            _num = _numeric_cols(_df_sb)
            x_col = st.selectbox("แกน X / Category", _all, index=0, key="sel_x")
            y_cols = st.multiselect(
                "แกน Y / Values (ตัวเลข)",
                _num,
                default=_num[: min(3, len(_num))],
                key="sel_y",
            )

# ---------------------------------------------------------------------------
# Guard: no file selected
# ---------------------------------------------------------------------------
if not chosen_path or not Path(chosen_path).is_file():
    st.markdown(
        """
        <div class="header-bar">
            <h1>📊 ระบบรายงานวิจัยประจำเดือน</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("👈 เลือกไฟล์ .xlsx จากแถบด้านซ้ายเพื่อเริ่มต้นใช้งาน")
    st.stop()

if not selected_sheet:
    st.warning("ไม่พบ sheet ในไฟล์ที่เลือก")
    st.stop()

# ---------------------------------------------------------------------------
# Load / cache data
# ---------------------------------------------------------------------------
mtime_now = _mtime(chosen_path)
cache_key = (chosen_path, selected_sheet, mtime_now)
if st.session_state.cached_key != cache_key:
    st.session_state.cached_df = _load(chosen_path, selected_sheet)
    st.session_state.cached_key = cache_key
    st.session_state.last_mtime = mtime_now

df: pd.DataFrame = st.session_state.cached_df

# ---------------------------------------------------------------------------
# Header with LIVE badge
# ---------------------------------------------------------------------------
live_badge = '<span class="live-badge">● LIVE</span>' if auto_refresh else ""
updated_str = (
    datetime.fromtimestamp(mtime_now).strftime("%d/%m/%Y %H:%M:%S")
    if mtime_now
    else "—"
)
st.markdown(
    f"""
    <div class="header-bar">
        <h1>📊 ระบบรายงานวิจัยประจำเดือน {live_badge}</h1>
        <small>
            📄 <b>{Path(chosen_path).name}</b> &nbsp;|&nbsp;
            📋 Sheet: <b>{selected_sheet}</b> &nbsp;|&nbsp;
            🕒 แก้ไขล่าสุด: <b>{updated_str}</b> &nbsp;|&nbsp;
            📐 <b>{len(df):,} แถว × {len(df.columns)} คอลัมน์</b>
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Summary Metrics
# ---------------------------------------------------------------------------
num_cols_all = _numeric_cols(df)
display_y = y_cols if y_cols else num_cols_all[:4]

if display_y:
    st.subheader("📌 สรุปตัวชี้วัด")
    cols_m = st.columns(min(len(display_y), 4))
    for i, col in enumerate(display_y[:4]):
        with cols_m[i]:
            s = df[col].dropna()
            st.metric(label=f"∑ {col}", value=_fmt(s.sum()))
            st.caption(
                f"เฉลี่ย {s.mean():,.2f}　｜　"
                f"นับ {len(s):,}　｜　"
                f"Max {s.max():,.2f}"
            )
    st.divider()

# ---------------------------------------------------------------------------
# Filter + Data Table
# ---------------------------------------------------------------------------
st.subheader("🗃️ ตารางข้อมูล")

with st.expander("🔍 กรองข้อมูล (Filter & Search)", expanded=False):
    search_text = st.text_input(
        "🔎 ค้นหา (ค้นทุก column)", placeholder="พิมพ์คำค้นหา…"
    )

    cat_cols = [
        c for c in df.columns if df[c].dtype == object and df[c].nunique() <= 40
    ]
    num_range_cols = num_cols_all[:3]

    filter_applied: dict = {}
    range_filters: dict = {}

    if cat_cols:
        n_fc = min(3, len(cat_cols))
        fc_cols = st.columns(n_fc)
        for i, c in enumerate(cat_cols[:6]):
            with fc_cols[i % n_fc]:
                uniq = sorted(df[c].dropna().astype(str).unique())
                sel = st.multiselect(c, uniq, key=f"f_cat_{c}")
                if sel:
                    filter_applied[c] = sel

    if num_range_cols:
        st.markdown("**ช่วงค่าตัวเลข**")
        nr_cols = st.columns(len(num_range_cols))
        for i, c in enumerate(num_range_cols):
            with nr_cols[i]:
                cmin, cmax = float(df[c].min()), float(df[c].max())
                if cmin < cmax:
                    lo, hi = st.slider(
                        c,
                        min_value=cmin,
                        max_value=cmax,
                        value=(cmin, cmax),
                        key=f"f_num_{c}",
                    )
                    if lo > cmin or hi < cmax:
                        range_filters[c] = (lo, hi)

filtered = df.copy()
if search_text:
    mask = filtered.astype(str).apply(
        lambda col: col.str.contains(search_text, case=False, na=False)
    ).any(axis=1)
    filtered = filtered[mask]
for col, vals in filter_applied.items():
    filtered = filtered[filtered[col].astype(str).isin(vals)]
for col, (lo, hi) in range_filters.items():
    filtered = filtered[filtered[col].between(lo, hi)]

st.dataframe(filtered, use_container_width=True, height=380)
st.caption(f"แสดง {len(filtered):,} จาก {len(df):,} แถว")
st.divider()

# ---------------------------------------------------------------------------
# Time-Series auto-detection
# ---------------------------------------------------------------------------
date_cols = _detect_date_cols(df)
if date_cols and num_cols_all:
    st.subheader("📅 Time-Series (ตรวจจับวันที่อัตโนมัติ)")
    ts_c1, ts_c2 = st.columns(2)
    with ts_c1:
        ts_date_col = st.selectbox("คอลัมน์วันที่", date_cols, key="ts_date")
    with ts_c2:
        ts_val_col = st.selectbox("ค่าที่ต้องการแสดง", num_cols_all, key="ts_val")

    if ts_date_col and ts_val_col:
        ts_df = df[[ts_date_col, ts_val_col]].copy().dropna()
        ts_df[ts_date_col] = pd.to_datetime(ts_df[ts_date_col], errors="coerce")
        ts_df = ts_df.dropna().sort_values(ts_date_col)
        if not ts_df.empty:
            fig_ts = px.line(
                ts_df,
                x=ts_date_col,
                y=ts_val_col,
                markers=True,
                template="plotly_white",
                height=340,
                title=f"{ts_val_col} ตามเวลา",
                color_discrete_sequence=["#1565C0"],
            )
            fig_ts.update_layout(margin=dict(l=20, r=20, t=50, b=40))
            st.plotly_chart(fig_ts, use_container_width=True)
    st.divider()

# ---------------------------------------------------------------------------
# Bar Chart + Line Chart
# ---------------------------------------------------------------------------
if not x_col or not display_y:
    st.info("เลือกแกน X และแกน Y ในแถบด้านซ้ายเพื่อแสดงกราฟ")
else:
    _y_avail = [c for c in display_y if c in filtered.columns]
    if x_col not in filtered.columns or not _y_avail:
        st.warning("ไม่พบคอลัมน์ที่เลือกในข้อมูลที่ถูกกรอง")
    else:
        chart_df = filtered[[x_col] + _y_avail].copy()
        chart_df[x_col] = chart_df[x_col].astype(str)

        col_bar, col_line = st.columns(2)
        common_layout = dict(
            legend_title_text="",
            xaxis_tickangle=-35,
            margin=dict(l=20, r=20, t=36, b=80),
        )

        with col_bar:
            st.subheader("📊 Bar Chart")
            fig_bar = px.bar(
                chart_df,
                x=x_col,
                y=_y_avail,
                barmode="group",
                template="plotly_white",
                height=420,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_bar.update_layout(**common_layout)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_line:
            st.subheader("📈 Line Chart")
            fig_line = px.line(
                chart_df,
                x=x_col,
                y=_y_avail,
                markers=True,
                template="plotly_white",
                height=420,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_line.update_layout(**common_layout)
            st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------------------------------
# Auto-refresh — must be last
# ---------------------------------------------------------------------------
if auto_refresh:
    with st.sidebar:
        st.caption(f"⏱ รีเฟรชอีกครั้งใน {refresh_sec} วินาที…")
    time.sleep(refresh_sec)
    st.rerun()
