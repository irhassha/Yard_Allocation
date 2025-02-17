import streamlit as st
import altair as alt
import pandas as pd
import math
from datetime import date, timedelta

# ---------------------------------------------------------------
# 1. Upload File Excel untuk Data Vessel
# ---------------------------------------------------------------
st.title("Container Yard Allocation - Excel Upload & Daily Receiving Rates")

uploaded_file = st.file_uploader("Upload Vessel Excel (dengan kolom: Vessel, Total_Containers, Cluster_Need, ETA, Berth)", type=["xlsx"])
if not uploaded_file:
    st.warning("Silakan upload file Excel terlebih dahulu.")
    st.stop()

df_vessels = pd.read_excel(uploaded_file)
# Pastikan kolom ETA dibaca sebagai string, lalu dikonversi dengan format yang sesuai.
if "ETA" in df_vessels.columns:
    df_vessels["ETA"] = df_vessels["ETA"].astype(str)
    # Misal data di Excel berupa 8-digit: YYYYMMDD, contohnya "20240206"
    df_vessels["ETA"] = pd.to_datetime(df_vessels["ETA"], format="%Y%m%d", errors="coerce")
else:
    st.error("Kolom 'ETA' tidak ditemukan.")
    st.stop()

st.subheader("Data Vessel (dari Excel)")
st.dataframe(df_vessels)

# Konversi ke list of dict
vessels_data = df_vessels.to_dict(orient="records")

# ---------------------------------------------------------------
# 2. Definisikan Receiving Rate Harian (D1-D7) untuk setiap kapal
#    (Dummy data; sesuaikan dengan data aslinya)
#    D1 = hari pertama penerimaan (misal 7 hari sebelum ETA), 
#    D2 = hari kedua, …, D7 = hari ke-7 (satu hari sebelum ETA)
receiving_rate_map = {
    "A": {1: 0.13, 2: 0.15, 3: 0.12, 4: 0.25, 5: 0.25, 6: 0.05, 7: 0.05},
    "B": {1: 0.12, 2: 0.17, 3: 0.21, 4: 0.30, 5: 0.10, 6: 0.07, 7: 0.03},
    "C": {1: 0.10, 2: 0.11, 3: 0.29, 4: 0.30, 5: 0.10, 6: 0.06, 7: 0.04},
    # Tambahkan kapal lain (D, E, ...) sesuai kebutuhan.
}

# ---------------------------------------------------------------
# 3. Fungsi Determine Cluster Need
#    (Jika Total <1000 => 3 cluster, <1500 => 2, else pakai nilai dari data)
# ---------------------------------------------------------------
def determine_cluster_need(total_c, cluster_c):
    if total_c < 1000:
        return 3
    elif total_c < 1500:
        return 2
    else:
        return cluster_c

# ---------------------------------------------------------------
# 4. Parameter Operasional
# ---------------------------------------------------------------
RECEIVING_DAYS = 7  # Penerimaan selama 7 hari (D1-D7)
CRANE_MOVE_PER_HOUR = 28
CRANE_COUNT = 2.7

def get_loading_days(total_containers):
    move_per_day = CRANE_MOVE_PER_HOUR * CRANE_COUNT * 24
    days = total_containers / move_per_day
    return math.ceil(days)

# ---------------------------------------------------------------
# 5. Info Block
# ---------------------------------------------------------------
blocks_info = {
    "A01": {"slots": 37, "max_per_slot": 30},
    "A02": {"slots": 37, "max_per_slot": 30},
    "A03": {"slots": 37, "max_per_slot": 30},
    "A04": {"slots": 37, "max_per_slot": 30},
    "A05": {"slots": 37, "max_per_slot": 30},
    "B01": {"slots": 37, "max_per_slot": 30},
    "B02": {"slots": 37, "max_per_slot": 30},
    "B03": {"slots": 37, "max_per_slot": 30},
    "B04": {"slots": 37, "max_per_slot": 30},
    "C01": {"slots": 45, "max_per_slot": 30},
    "C02": {"slots": 45, "max_per_slot": 30},
    "C03": {"slots": 45, "max_per_slot": 30},
}

def get_block_prefix_order(berth):
    if berth == "NP1":
        return ["A","B","C"]
    elif berth == "NP2":
        return ["B","A","C"]
    elif berth == "NP3":
        return ["C","B","A"]
    else:
        return ["A","B","C"]

# ---------------------------------------------------------------
# 6. Sort Vessel Data & Buat Timeline
# ---------------------------------------------------------------
vessels_data = sorted(vessels_data, key=lambda x: x["ETA"])
min_eta = min(v["ETA"] for v in vessels_data)
max_eta = max(v["ETA"] for v in vessels_data)
start_date = min_eta - timedelta(days=RECEIVING_DAYS)
end_date = max_eta + timedelta(days=30)

all_days = []
cur = start_date
while cur <= end_date:
    all_days.append(cur)
    cur += timedelta(days=1)

# ---------------------------------------------------------------
# 7. Buat all_slots (Dynamic) – Menyusun slot untuk yard
# ---------------------------------------------------------------
all_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        all_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "containers": {}  # akan diisi dengan cluster allocation
        })

# ---------------------------------------------------------------
# 8. Buat vessel_states (Dynamic) – Menyusun status tiap kapal
# ---------------------------------------------------------------
vessel_states = {}
for v in vessels_data:
    v_name = v["Vessel"]
    total_c = math.ceil(v["Total_Containers"])
    cluster_c = v["Cluster_Need"]
    needed_cluster = determine_cluster_need(total_c, cluster_c)
    
    base_c = total_c // needed_cluster
    rem = total_c % needed_cluster
    clusters = []
    for i in range(needed_cluster):
        size_ = base_c + (1 if i < rem else 0)
        clusters.append({
            "cluster_label": f"{v_name}-C{i+1}",
            "size": size_,
            "remain": size_,
        })
    
    eta = v["ETA"]
    load_days = get_loading_days(total_c)
    start_load = eta
    end_load = eta + timedelta(days=load_days - 1)
    
    vessel_states[v_name] = {
        "Vessel": v_name,
        "Total": total_c,
        "ETA": eta,
        "Berth": v["Berth"],
        "Clusters": clusters,
        "start_receive": eta - timedelta(days=RECEIVING_DAYS),
        "end_receive": eta - timedelta(days=1),
        "start_load": start_load,
        "end_load": end_load,
        "done": False
    }

# ---------------------------------------------------------------
# 9. Fungsi Hindari Clash (ETA < 3 hari)
# ---------------------------------------------------------------
block_usage = {}

def is_clashing(this_vessel, block, margin=3):
    if block not in block_usage:
        return False
    this_eta = vessel_states[this_vessel]["ETA"]
    for (other_vessel, other_eta) in block_usage[block]:
        if abs((this_eta - other_eta).days) < margin:
            return True
    return False

def mark_block_usage(vessel, block):
    v_eta = vessel_states[vessel]["ETA"]
    if block not in block_usage:
        block_usage[block] = []
    block_usage[block].append((vessel, v_eta))

# ---------------------------------------------------------------
# 10. Fungsi Alokasi (Dynamic)
# ---------------------------------------------------------------
def allocate_with_preference(cluster_label, qty, vessel_name):
    berth = vessel_states[vessel_name]["Berth"]
    prefix_order = get_block_prefix_order(berth)
    remaining = qty
    
    for pfx in prefix_order:
        if remaining <= 0:
            break
        block_slots_map = {}
        for slot in all_slots:
            if slot["block"].startswith(pfx):
                block_slots_map.setdefault(slot["block"], []).append(slot)
        
        for block_name in sorted(block_slots_map.keys()):
            if remaining <= 0:
                break
            if is_clashing(vessel_name, block_name):
                continue
            for slot in block_slots_map[block_name]:
                if remaining <= 0:
                    break
                used = sum(slot["containers"].values())
                free_capacity = slot["capacity_per_slot"] - used
                if free_capacity > 0:
                    can_fill = min(free_capacity, remaining)
                    slot["containers"].setdefault(cluster_label, 0)
                    slot["containers"][cluster_label] += can_fill
                    remaining -= can_fill
            if remaining < qty:
                mark_block_usage(vessel_name, block_name)
    
    return remaining

def remove_cluster_containers(cluster_label, qty):
    remaining = qty
    for slot in all_slots:
        if remaining <= 0:
            break
        if cluster_label in slot["containers"]:
            available = slot["containers"][cluster_label]
            take = min(available, remaining)
            slot["containers"][cluster_label] -= take
            remaining -= take
            if slot["containers"][cluster_label] <= 0:
                del slot["containers"][cluster_label]
    return remaining

# ---------------------------------------------------------------
# 11. Simulasi Dynamic Allocation (menggunakan receiving rate harian)
# ---------------------------------------------------------------
snapshots_map = {}  # Simpan snapshot yard untuk setiap hari (key: tanggal)

for d in all_days:
    # Tandai kapal yang sudah melewati end_load => done
    for v_name, stt in vessel_states.items():
        if not stt["done"] and d > stt["end_load"]:
            stt["done"] = True
    
    # Receiving
    for v_name, stt in vessel_states.items():
        if stt["done"]:
            continue
        if stt["start_receive"] <= d <= stt["end_receive"]:
            # day_idx = (d - start_receive).days + 1, yang seharusnya 1..7
            day_idx = (d - stt["start_receive"]).days + 1
            rate = 0.0
            if v_name in receiving_rate_map and day_idx in receiving_rate_map[v_name]:
                rate = receiving_rate_map[v_name][day_idx]
            daily_in = math.ceil(stt["Total"] * rate)
            for c in stt["Clusters"]:
                if c["remain"] > 0:
                    # Alokasi proporsional untuk cluster
                    portion = math.ceil(daily_in * (c["size"] / stt["Total"]))
                    portion = min(portion, c["remain"])
                    if portion > 0:
                        leftover = allocate_with_preference(c["cluster_label"], portion, v_name)
                        allocated = portion - leftover
                        c["remain"] -= allocated
                        if allocated > 0:
                            snapshots_map.setdefault(d, [])
                            # Catat log (misal: "[RECV D{day_idx}] ...")
    # Loading
    for v_name, stt in vessel_states.items():
        if stt["done"]:
            continue
        if stt["start_load"] <= d <= stt["end_load"]:
            ld = get_loading_days(stt["Total"])
            daily_out = math.ceil(stt["Total"] / ld)
            for c in stt["Clusters"]:
                portion_out = math.ceil(daily_out * (c["size"] / stt["Total"]))
                leftover_remove = remove_cluster_containers(c["cluster_label"], portion_out)
                removed = portion_out - leftover_remove
                # (Log events bisa ditambahkan di sini jika diinginkan)
    # Tandai selesai loading
    for v_name, stt in vessel_states.items():
        if not stt["done"] and stt["end_load"] == d:
            stt["done"] = True
    # Simpan snapshot hari ini
    snapshot = []
    for slot in all_slots:
        total_in_slot = sum(slot["containers"].values())
        detail_dict = dict(slot["containers"])
        snapshot.append({
            "slot_id": slot["slot_id"],
            "total": total_in_slot,
            "detail": detail_dict
        })
    snapshots_map[d] = snapshot

# ---------------------------------------------------------------
# 12. Static Allocation (Overlapping)
# ---------------------------------------------------------------
static_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        static_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "allocations": []
        })

vessels_sorted = sorted(vessels_data, key=lambda x: x["ETA"])
for v in vessels_sorted:
    remaining = math.ceil(v["Total_Containers"])
    vname = v["Vessel"]
    for slot in static_slots:
        used = sum(a[1] for a in slot["allocations"])
        free_cap = slot["capacity_per_slot"] - used
        if free_cap > 0:
            can_fill = min(free_cap, remaining)
            slot["allocations"].append((vname, can_fill))
            remaining -= can_fill
        if remaining <= 0:
            break

max_alloc = max(len(s["allocations"]) for s in static_slots)
static_table_rows = []
for s in static_slots:
    row = {"Slot": s["slot_id"]}
    for i in range(max_alloc):
        col_name = f"Vessel {i+1}"
        if i < len(s["allocations"]):
            (vv, amt) = s["allocations"][i]
            row[col_name] = f"{vv}({amt})"
        else:
            row[col_name] = ""
    static_table_rows.append(row)
df_static = pd.DataFrame(static_table_rows)

# ---------------------------------------------------------------
# 13. Fungsi Visualisasi
# ---------------------------------------------------------------
def prepare_visual_dynamic(snapshot):
    rows = []
    for slot_info in snapshot:
        sid = slot_info["slot_id"]
        parts = sid.split("-")
        block_name = parts[0]
        slot_num = int(parts[1])
        detail = slot_info["detail"]
        if not detail:
            occupant_label = ""
        elif len(detail) == 1:
            occupant_label = list(detail.keys())[0]
        else:
            occupant_label = "+".join(detail.keys())
        rows.append({
            "block": block_name,
            "slot": slot_num,
            "slot_str": str(slot_num),
            "occupant": occupant_label
        })
    return pd.DataFrame(rows)

def prepare_visual_static(df_static):
    rows = []
    for i, row in df_static.iterrows():
        sid = row["Slot"]
        parts = sid.split("-")
        block_name = parts[0]
        slot_num = int(parts[1])
        occupant_list = []
        for col in df_static.columns:
            if col.startswith("Vessel "):
                val = row[col]
                if isinstance(val, str) and val.strip():
                    vessel = val.split("(")[0]
                    occupant_list.append(vessel)
        if not occupant_list:
            occupant_label = ""
        elif len(occupant_list) == 1:
            occupant_label = occupant_list[0]
        else:
            occupant_label = "+".join(occupant_list)
        rows.append({
            "block": block_name,
            "slot": slot_num,
            "slot_str": str(slot_num),
            "occupant": occupant_label
        })
    return pd.DataFrame(rows)

def parse_occupant_vessels(occupant_str):
    if not occupant_str:
        return []
    parts = occupant_str.split("+")
    vessel_list = []
    for p in parts:
        if "-" in p:
            vessel_list.append(p.split("-")[0])
        else:
            vessel_list.append(p)
    return vessel_list

def filter_vessels(df, selected_vessels):
    if not selected_vessels:
        return df[0:0]
    filtered = []
    for i, row in df.iterrows():
        occ = row["occupant"]
        occ_list = parse_occupant_vessels(occ)
        if set(occ_list).intersection(set(selected_vessels)):
            filtered.append(row)
    return pd.DataFrame(filtered)

# Visualisasi: Tiga grup chart (Group C, B, A) secara side-by-side dengan layered chart (rect + text)
def visualize_blocks_side_by_side(df, chart_title):
    def make_chart(df_sub, block_list, sub_title):
        data_sub = df_sub[df_sub["block"].isin(block_list)].copy()
        data_sub["slot_str"] = data_sub["slot"].astype(str)
        
        base = alt.Chart(data_sub).encode(
            x=alt.X("slot_str:O", sort=alt.SortField(field="slot", order="ascending"), title="Slot"),
            y=alt.Y("block:N", sort=block_list, title="Block"),
            tooltip=["block", "slot", "occupant"]
        )
        
        rect = base.mark_rect().encode(
            color=alt.Color("occupant:N", legend=alt.Legend(
                title="Vessel Assignments", orient="bottom", direction="horizontal"
            ))
        )
        
        text = base.mark_text(
            align="center",
            baseline="middle",
            color="black"
        ).encode(
            text="occupant:N"
        )
        
        chart = (rect + text).properties(
            width=200,
            height=200,
            title=sub_title
        )
        return chart
    
    # Definisikan grup block sesuai urutan (ubah sesuai kebutuhan)
    blocks_C = ["C01", "C02", "C03"]
    blocks_B = ["B04", "B03", "B02", "B01"]
    blocks_A = ["A05", "A04", "A03", "A02", "A01"]
    
    chart_c = make_chart(df, blocks_C, "Group C")
    chart_b = make_chart(df, blocks_B, "Group B")
    chart_a = make_chart(df, blocks_A, "Group A")
    
    final_chart = alt.hconcat(chart_c, chart_b, chart_a, spacing=40).properties(title=chart_title)
    return final_chart

# ---------------------------------------------------------------
# 14. Tampilan di Streamlit
# ---------------------------------------------------------------
st.subheader("Log Events (Dynamic)")
st.dataframe(df_log)

mode = st.radio("Pilih Mode", ["Dynamic", "Static"], index=0)

all_vessels = [v["Vessel"] for v in vessels_data]
vessel_choice = st.multiselect("Filter Vessel", all_vessels, default=all_vessels)

if mode == "Dynamic":
    st.subheader("Dynamic Snapshot")
    day_choice = st.selectbox("Pilih Tanggal Snapshot", sorted(snapshots_map.keys()))
    chosen_snapshot = snapshots_map[day_choice]
    df_dyn = prepare_visual_dynamic(chosen_snapshot)
    df_dyn_filtered = filter_vessels(df_dyn, vessel_choice)
    chart_dyn = visualize_blocks_side_by_side(df_dyn_filtered, f"Dynamic Allocation - {day_choice}")
    st.altair_chart(chart_dyn, use_container_width=True)
else:
    st.subheader("Static Allocation Table")
    st.dataframe(df_static)
    df_stat = prepare_visual_static(df_static)
    df_stat_filtered = filter_vessels(df_stat, vessel_choice)
    chart_stat = visualize_blocks_side_by_side(df_stat_filtered, "Static Allocation Layout")
    st.altair_chart(chart_stat, use_container_width=True)

st.write("""
**Penjelasan:**
- Data vessel diambil dari file Excel yang diupload.
- ETA dikonversi menggunakan format '%Y%m%d' sehingga misalnya '20240206' terbaca sebagai 2024-02-06.
- Receiving Rate harian didefinisikan secara dummy di dalam script untuk setiap kapal (D1–D7).
- Dynamic allocation mensimulasikan penerimaan dan loading berdasarkan timeline.
- Static allocation mengalokasikan seluruh kontainer sekaligus (tanpa timeline).
- Visualisasi ditampilkan dalam 3 grup chart: Group C (blok C), Group B (blok B), Group A (blok A), dengan legend di bawah dan teks occupant di dalam sel.
- Filter Vessel memungkinkan hanya menampilkan slot yang memuat kapal yang dipilih.
""")