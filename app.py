"""
Excel File Dashboard — Streamlit
รองรับ: File Selector, Live Update, Auto-detect columns, Summary + Charts
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
    page_title="Excel Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "last_mtime": None,
    "cached_df": None,
    "cached_key": None,   # (filepath, sheet) tuple
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    if not p.exists():
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
    if isinstance(val, (int,)):
        return f"{val:,}"
    return str(val)


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ การตั้งค่า")
    st.divider()

    # --- Folder path ---
    default_folder = str(Path(__file__).parent / "data")
    folder_path = st.text_input(
        "📁 โฟลเดอร์ไฟล์ .xlsx",
        value=default_folder,
        help=(
            "ระบุ path ของโฟลเดอร์\n\n"
            "Windows ตัวอย่าง:\n"
            r"C:\Users\urfco\OneDrive\Desktop\รองคณบดีผ่ายวิจัย\รายงานวิจัยประจำเดือน\รายงานหน่วยวิจัย"
        ),
    )

    st.divider()

    # --- File source ---
    src_tab_folder, src_tab_upload = st.tabs(["📂 เลือกจากโฟลเดอร์", "⬆️ อัปโหลด"])
    chosen_path: str | None = None

    with src_tab_folder:
        xlsx_list = _list_xlsx(folder_path)
        if xlsx_list:
            picked_name = st.selectbox("เลือกไฟล์", xlsx_list, key="sel_file")
            chosen_path = str(Path(folder_path) / picked_name)
        else:
            st.info("ไม่พบไฟล์ .xlsx ในโฟลเดอร์ที่ระบุ")

    with src_tab_upload:
        uploaded = st.file_uploader("อัปโหลดไฟล์ .xlsx", type=["xlsx"])
        if uploaded:
            dest = Path(folder_path)
            dest.mkdir(parents=True, exist_ok=True)
            save_path = dest / uploaded.name
            save_path.write_bytes(uploaded.getvalue())
            chosen_path = str(save_path)
            st.success(f"บันทึก: {uploaded.name}")

    st.divider()

    # --- Sheet selector ---
    sheet_names: list[str] = []
    selected_sheet: str | None = None
    if chosen_path and Path(chosen_path).exists():
        sheet_names = _sheet_names(chosen_path)
    if sheet_names:
        selected_sheet = st.selectbox("📋 เลือก Sheet", sheet_names, key="sel_sheet")
    elif chosen_path:
        st.warning("ไม่พบ sheet ในไฟล์นี้")

    st.divider()

    # --- Live update ---
    st.subheader("🔄 Live Update")
    auto_refresh = st.toggle("เปิด Auto Refresh", value=False)
    refresh_sec = st.slider(
        "อัปเดตทุก (วินาที)", 5, 120, 15, disabled=not auto_refresh
    )

    st.divider()

    # --- Chart column selectors (populated after data load) ---
    st.subheader("📈 ตั้งค่ากราฟ")
    x_col: str | None = None
    y_cols: list[str] = []

    if chosen_path and selected_sheet and Path(chosen_path).exists():
        _mtime_now = _mtime(chosen_path)
        _cache_key = (chosen_path, selected_sheet, _mtime_now)
        if st.session_state.cached_key != _cache_key:
            st.session_state.cached_df = _load(chosen_path, selected_sheet)
            st.session_state.cached_key = _cache_key
            if (
                st.session_state.last_mtime is not None
                and _mtime_now != st.session_state.last_mtime
            ):
                st.toast("🔄 ไฟล์มีการเปลี่ยนแปลง — โหลดข้อมูลใหม่แล้ว", icon="✅")
            st.session_state.last_mtime = _mtime_now

        _df_sidebar = st.session_state.cached_df
        if _df_sidebar is not None:
            _all_cols = _df_sidebar.columns.tolist()
            _num_cols = _numeric_cols(_df_sidebar)
            x_col = st.selectbox(
                "แกน X / Category", _all_cols, index=0, key="sel_x"
            )
            y_cols = st.multiselect(
                "แกน Y / Values (ตัวเลข)",
                _num_cols,
                default=_num_cols[: min(3, len(_num_cols))],
                key="sel_y",
            )

# ---------------------------------------------------------------------------
# Guard: no file loaded
# ---------------------------------------------------------------------------
if not chosen_path or not Path(chosen_path).exists():
    st.title("📊 Excel File Dashboard")
    st.info("👈 เลือกไฟล์ .xlsx จากแถบด้านซ้ายเพื่อเริ่มต้นใช้งาน")
    st.stop()

if not selected_sheet:
    st.warning("ไม่พบ sheet ในไฟล์ที่เลือก")
    st.stop()

# ---------------------------------------------------------------------------
# Load / retrieve data
# ---------------------------------------------------------------------------
mtime_now = _mtime(chosen_path)
cache_key = (chosen_path, selected_sheet, mtime_now)
if st.session_state.cached_key != cache_key:
    st.session_state.cached_df = _load(chosen_path, selected_sheet)
    st.session_state.cached_key = cache_key
    st.session_state.last_mtime = mtime_now

df: pd.DataFrame = st.session_state.cached_df

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📊 Excel File Dashboard")

info_c1, info_c2, info_c3, info_c4 = st.columns(4)
info_c1.caption(f"📄 ไฟล์: **{Path(chosen_path).name}**")
info_c2.caption(f"📋 Sheet: **{selected_sheet}**")
info_c3.caption(
    f"🕒 แก้ไขล่าสุด: **"
    f"{datetime.fromtimestamp(mtime_now).strftime('%d/%m/%Y %H:%M:%S')}**"
    if mtime_now else "🕒 —"
)
info_c4.caption(f"📐 {len(df):,} แถว × {len(df.columns)} คอลัมน์")

st.divider()

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
num_cols_all = _numeric_cols(df)
display_y = y_cols if y_cols else num_cols_all[:4]

if display_y:
    st.subheader("📌 Summary Metrics")
    metric_cols = st.columns(len(display_y))
    for i, col in enumerate(display_y):
        with metric_cols[i]:
            series = df[col].dropna()
            st.metric(label=f"∑ {col}", value=_fmt(series.sum()))
            st.caption(
                f"เฉลี่ย {series.mean():,.2f}　|　"
                f"นับ {len(series):,}　|　"
                f"Max {series.max():,.2f}"
            )
    st.divider()

# ---------------------------------------------------------------------------
# Filter + Data Table
# ---------------------------------------------------------------------------
st.subheader("🗃️ ตารางข้อมูล")

with st.expander("🔍 กรองข้อมูล (Filter)", expanded=False):
    cat_cols = [c for c in df.columns if df[c].dtype == object and df[c].nunique() <= 40]
    num_range_cols = num_cols_all[:3]

    filter_applied: dict[str, list] = {}
    range_filters: dict[str, tuple] = {}

    if cat_cols:
        fc_cols = st.columns(min(3, len(cat_cols)))
        for i, c in enumerate(cat_cols[:6]):
            with fc_cols[i % 3]:
                uniq = sorted(df[c].dropna().astype(str).unique())
                sel = st.multiselect(c, uniq, key=f"f_cat_{c}")
                if sel:
                    filter_applied[c] = sel

    if num_range_cols:
        st.markdown("**ช่วงค่าตัวเลข**")
        nr_cols = st.columns(len(num_range_cols))
        for i, c in enumerate(num_range_cols):
            with nr_cols[i]:
                col_min = float(df[c].min())
                col_max = float(df[c].max())
                if col_min < col_max:
                    lo, hi = st.slider(
                        c,
                        min_value=col_min,
                        max_value=col_max,
                        value=(col_min, col_max),
                        key=f"f_num_{c}",
                    )
                    if lo > col_min or hi < col_max:
                        range_filters[c] = (lo, hi)

filtered = df.copy()
for col, vals in filter_applied.items():
    filtered = filtered[filtered[col].astype(str).isin(vals)]
for col, (lo, hi) in range_filters.items():
    filtered = filtered[filtered[col].between(lo, hi)]

st.dataframe(filtered, use_container_width=True, height=380)
st.caption(f"แสดง {len(filtered):,} จาก {len(df):,} แถว")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
if not x_col or not display_y:
    st.info("เลือกแกน X และแกน Y ในแถบด้านซ้ายเพื่อแสดงกราฟ")
else:
    chart_data = filtered[[x_col] + [c for c in display_y if c in filtered.columns]].copy()
    chart_data[x_col] = chart_data[x_col].astype(str)

    col_bar, col_line = st.columns(2)

    with col_bar:
        st.subheader("📊 Bar Chart")
        fig_bar = px.bar(
            chart_data,
            x=x_col,
            y=display_y,
            barmode="group",
            template="plotly_white",
            height=420,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_bar.update_layout(
            legend_title_text="",
            xaxis_tickangle=-35,
            margin=dict(l=20, r=20, t=30, b=60),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_line:
        st.subheader("📈 Line Chart")
        fig_line = px.line(
            chart_data,
            x=x_col,
            y=display_y,
            markers=True,
            template="plotly_white",
            height=420,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_line.update_layout(
            legend_title_text="",
            xaxis_tickangle=-35,
            margin=dict(l=20, r=20, t=30, b=60),
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ---------------------------------------------------------------------------
# Auto-refresh (ต้องอยู่ท้ายสุดเสมอ)
# ---------------------------------------------------------------------------
if auto_refresh:
    with st.sidebar:
        st.caption(f"⏱ รีเฟรชอีกครั้งใน {refresh_sec} วินาที…")
    time.sleep(refresh_sec)
    st.rerun()
