"""
สร้างไฟล์ตัวอย่าง .xlsx ที่จำลองโครงสร้างรายงานหน่วยวิจัยรายเดือน
(เลียนแบบไฟล์ 'ข้อมูลเดือนมีนาคม 2569.xlsx')
"""
import pandas as pd
import numpy as np
from pathlib import Path

rng = np.random.default_rng(42)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# ---- Sheet 1: ข้อมูลโครงการวิจัย ----------------------------------------
research_units = [
    "หน่วยวิจัยนวัตกรรมวัสดุ",
    "หน่วยวิจัยพลังงานทดแทน",
    "หน่วยวิจัยสิ่งแวดล้อมและความยั่งยืน",
    "หน่วยวิจัยปัญญาประดิษฐ์และหุ่นยนต์",
    "หน่วยวิจัยเทคโนโลยีชีวภาพ",
    "หน่วยวิจัยวิศวกรรมโยธาและโครงสร้าง",
]

funding_sources = [
    "สำนักงานการวิจัยแห่งชาติ (วช.)",
    "สำนักงาน สกสว.",
    "ทุนมหาวิทยาลัย",
    "ภาคเอกชน",
    "ทุน Newton Fund",
    "ทุน EU Horizon",
]

statuses = ["กำลังดำเนินการ", "เสร็จสิ้น", "รอการอนุมัติ", "ล่าช้า"]

projects = []
for i in range(1, 31):
    unit = rng.choice(research_units)
    budget = int(rng.integers(200_000, 5_000_000))
    disbursed = int(budget * rng.uniform(0.1, 1.0))
    progress = int(rng.integers(5, 101))
    status = "เสร็จสิ้น" if progress == 100 else rng.choice(
        statuses[:3] if progress >= 50 else statuses
    )
    projects.append({
        "รหัสโครงการ": f"RES-2569-{i:03d}",
        "ชื่อโครงการวิจัย": f"โครงการวิจัยที่ {i}: {'นวัตกรรม' if i % 2 == 0 else 'การพัฒนา'}",
        "หน่วยวิจัย": unit,
        "ผู้วิจัยหลัก": f"รศ.ดร. นักวิจัย {i:02d}",
        "แหล่งทุน": rng.choice(funding_sources),
        "งบประมาณ (บาท)": budget,
        "เบิกจ่ายแล้ว (บาท)": disbursed,
        "ความก้าวหน้า (%)": progress,
        "สถานะ": status,
        "ผลงานตีพิมพ์ (ISI)": int(rng.integers(0, 5)),
        "ผลงานตีพิมพ์ (TCI)": int(rng.integers(0, 8)),
        "สิทธิบัตร/อนุสิทธิบัตร": int(rng.integers(0, 3)),
        "วันที่เริ่มต้น": pd.Timestamp("2568-10-01") + pd.Timedelta(days=int(rng.integers(0, 180))),
        "วันสิ้นสุดโครงการ": pd.Timestamp("2569-09-30"),
    })

df_projects = pd.DataFrame(projects)

# ---- Sheet 2: สรุปรายหน่วยวิจัย ------------------------------------------
summary_rows = []
for unit in research_units:
    unit_df = df_projects[df_projects["หน่วยวิจัย"] == unit]
    summary_rows.append({
        "หน่วยวิจัย": unit,
        "จำนวนโครงการ": len(unit_df),
        "งบประมาณรวม (บาท)": unit_df["งบประมาณ (บาท)"].sum(),
        "เบิกจ่ายรวม (บาท)": unit_df["เบิกจ่ายแล้ว (บาท)"].sum(),
        "ความก้าวหน้าเฉลี่ย (%)": round(unit_df["ความก้าวหน้า (%)"].mean(), 1),
        "ผลงานตีพิมพ์ ISI รวม": unit_df["ผลงานตีพิมพ์ (ISI)"].sum(),
        "ผลงานตีพิมพ์ TCI รวม": unit_df["ผลงานตีพิมพ์ (TCI)"].sum(),
        "สิทธิบัตรรวม": unit_df["สิทธิบัตร/อนุสิทธิบัตร"].sum(),
    })
df_summary = pd.DataFrame(summary_rows)

# ---- Sheet 3: ข้อมูลรายเดือน (ย้อนหลัง 12 เดือน) ------------------------
thai_months = [
    "เมษายน 2568", "พฤษภาคม 2568", "มิถุนายน 2568",
    "กรกฎาคม 2568", "สิงหาคม 2568", "กันยายน 2568",
    "ตุลาคม 2568", "พฤศจิกายน 2568", "ธันวาคม 2568",
    "มกราคม 2569", "กุมภาพันธ์ 2569", "มีนาคม 2569",
]
base_budget = 1_500_000
monthly_data = []
for i, month in enumerate(thai_months):
    monthly_data.append({
        "เดือน": month,
        "โครงการสะสม": 15 + i * 2,
        "งบประมาณเบิกจ่าย (บาท)": int(base_budget * (1 + i * 0.08) + rng.integers(-200_000, 200_000)),
        "ผลงานตีพิมพ์สะสม": i * 3 + int(rng.integers(0, 4)),
        "นักวิจัยที่เข้าร่วม": 40 + i + int(rng.integers(-3, 5)),
        "โครงการเสร็จสิ้น": i * 1 + int(rng.integers(0, 2)),
    })
df_monthly = pd.DataFrame(monthly_data)

# ---- Write Excel ----------------------------------------------------------
out_path = data_dir / "ข้อมูลเดือนมีนาคม 2569.xlsx"
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df_projects.to_excel(writer, sheet_name="ข้อมูลโครงการวิจัย", index=False)
    df_summary.to_excel(writer, sheet_name="สรุปรายหน่วยวิจัย", index=False)
    df_monthly.to_excel(writer, sheet_name="ข้อมูลรายเดือน", index=False)

print(f"✅ Created: {out_path}")
print(f"   Sheets: ข้อมูลโครงการวิจัย ({len(df_projects)} rows), "
      f"สรุปรายหน่วยวิจัย ({len(df_summary)} rows), "
      f"ข้อมูลรายเดือน ({len(df_monthly)} rows)")
