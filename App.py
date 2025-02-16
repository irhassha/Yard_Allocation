import streamlit as st
import altair as alt
import pandas as pd
import math
from datetime import date, timedelta

# ---------------------------------------------------------------
# 1. Data Awal
# ---------------------------------------------------------------
vessels_data = [
    {"Vessel": "A", "Total_Containers": 3760, "Cluster_Need": 4, "ETA": date(2024, 2, 6), "Berth": "NP1"},
    {"Vessel": "B", "Total_Containers": 842,  "Cluster_Need": 2, "ETA": date(2024, 2, 6), "Berth": "NP1"},
    {"Vessel": "C", "Total_Containers": 539,  "Cluster_Need": 2, "ETA": date(2024, 2, 7), "Berth": "NP1"},
    {"Vessel": "D", "Total_Containers": 1021, "Cluster_Need": 3, "ETA": date(2024, 2, 7), "Berth": "NP1"},
    {"Vessel": "E", "Total_Containers": 1350, "Cluster_Need": 4, "ETA": date(2024, 2, 8), "Berth": "NP1"},
    {"Vessel": "F", "Total_Containers": 639,  "Cluster_Need": 2, "ETA": date(2024, 2, 8), "Berth": "NP1"},
    {"Vessel": "G", "Total_Containers": 1091, "Cluster_Need": 2, "ETA": date(2024, 2, 9), "Berth": "NP2"},
    {"Vessel": "H", "Total_Containers": 1002, "Cluster_Need": 3, "ETA": date(2024, 2, 9), "Berth": "NP2"},
    {"Vessel": "I", "Total_Containers": 1019, "Cluster_Need": 2, "ETA": date(2024, 2, 10), "Berth": "NP2"},
    {"Vessel": "J", "Total_Containers": 983,  "Cluster_Need": 2, "ETA": date(2024, 2, 10), "Berth": "NP2"},
    {"Vessel": "K", "Total_Containers": 667,  "Cluster_Need": 1, "ETA": date(2024, 2, 11), "Berth": "NP3"},
    {"Vessel": "L", "Total_Containers": 952,  "Cluster_Need": 2, "ETA": date(2024, 2, 11), "Berth": "NP3"},
    {"Vessel": "M", "Total_Containers": 1302, "Cluster_Need": 2, "ETA": date(2024, 2, 12), "Berth": "NP1"},
    {"Vessel": "N", "Total_Containers": 538,  "Cluster_Need": 1, "ETA": date(2024, 2, 12), "Berth": "NP2"},
    {"Vessel": "O", "Total_Containers": 1204, "Cluster_Need": 3, "ETA": date(2024, 2, 12), "Berth": "NP3"},
    {"Vessel": "P", "Total_Containers": 1298, "Cluster_Need": 3, "ETA": date(2024, 2, 12), "Berth": "NP1"},
]

# ---------------------------------------------------------------
# 2. Info Block & Preferensi
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
        return ["A", "B", "C"]
    elif berth == "NP2":
        return ["B", "A", "C"]
    elif berth == "NP3":
        return ["C", "B", "A"]
    else:
        return ["A", "B", "C"]

# ---------------------------------------------------------------
# 3. all_slots untuk Dynamic Approach
# ---------------------------------------------------------------
all_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        all_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "containers": {}  # {cluster_label: qty}
        })

# ---------------------------------------------------------------
# 4. Aturan Minimal Cluster
# ---------------------------------------------------------------
def determine_cluster_need(total_from_data, cluster_from_data):
    if total_from_data < 1000:
        return 3
    elif total_from_data < 1500:
        return 2
    else:
        return cluster_from_data

# ---------------------------------------------------------------
# 5. Parameter Operasional
# ---------------------------------------------------------------
RECEIVING_DAYS = 7
RECEIVING_RATE = 0.12
CRANE_MOVE_PER_HOUR = 28
CRANE_COUNT = 2.7

def get_loading_days(total_containers):
    move_per_day = CRANE_MOVE_PER_HOUR * CRANE_COUNT * 24
    days = total_containers / move_per_day
    return math.ceil(days)

# ---------------------------------------------------------------
# 6. Timeline (Day-by-Day)
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
# 7. vessel_states untuk Dynamic
# ---------------------------------------------------------------
vessel_states = {}
for v in vessels_data:
    v_name = v["Vessel"]
    total_c = math.ceil(v["Total_Containers"])
    needed_cluster = determine_cluster_need(total_c, v["Cluster_Need"])
    base_csize = total_c // needed_cluster
    rem = total_c % needed_cluster
    
    clusters = []
    for i in range(needed_cluster):
        size_ = base_csize + (1 if i < rem else 0)
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
# 8. Hindari Clash ETA < 3 Hari (Dynamic)
# ---------------------------------------------------------------
block_usage = {}

def is_clashing(this_vessel, block, states, margin_days=3):
    if block not in block_usage:
        return False
    this_eta = states[this_vessel]["ETA"]
    for (other_vessel, other_eta) in block_usage[block]:
        if abs((this_eta - other_eta).days) < margin_days:
            return True
    return False

def mark_block_usage(vessel, block):
    v_eta = vessel_states[vessel]["ETA"]
    if block not in block_usage:
        block_usage[block] = []
    block_usage[block].append((vessel, v_eta))

# ---------------------------------------------------------------
# 9. Fungsi Alokasi & Remove (Dynamic)
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
            if is_clashing(vessel_name, block_name, vessel_states):
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
# 10. Simulasi Dynamic Day-by-Day + Snapshot
# ---------------------------------------------------------------
yard_snapshots = {}
log_events = []

for d in all_days:
    # 1. Tandai done kalau lewat end_load
    for v_name, v_state in vessel_states.items():
        if not v_state["done"] and d > v_state["end_load"]:
            v_state["done"] = True
    
    # 2. Receiving
    for v_name, v_state in vessel_states.items():
        if v_state["done"]:
            continue
        if v_state["start_receive"] <= d <= v_state["end_receive"]:
            daily_in = math.ceil(v_state["Total"] * RECEIVING_RATE)
            for c in v_state["Clusters"]:
                if c["remain"] > 0:
                    portion = math.ceil(daily_in * (c["size"] / v_state["Total"]))
                    portion = min(portion, c["remain"])
                    if portion > 0:
                        leftover = allocate_with_preference(c["cluster_label"], portion, v_name)
                        allocated = portion - leftover
                        c["remain"] -= allocated
                        if allocated > 0:
                            log_events.append((d, f"[RECV] {allocated} to {c['cluster_label']}"))
        elif d == v_state["ETA"]:
            for c in v_state["Clusters"]:
                if c["remain"] > 0:
                    leftover = allocate_with_preference(c["cluster_label"], c["remain"], v_name)
                    allocated = c["remain"] - leftover
                    c["remain"] -= allocated
                    if allocated > 0:
                        log_events.append((d, f"[RECV-FINAL] {allocated} to {c['cluster_label']}"))
    
    # 3. Loading
    for v_name, v_state in vessel_states.items():
        if v_state["done"]:
            continue
        if v_state["start_load"] <= d <= v_state["end_load"]:
            ld = get_loading_days(v_state["Total"])
            daily_out = math.ceil(v_state["Total"] / ld)
            for c in v_state["Clusters"]:
                portion_out = math.ceil(daily_out * (c["size"] / v_state["Total"]))
                leftover_remove = remove_cluster_containers(c["cluster_label"], portion_out)
                removed = portion_out - leftover_remove
                if removed > 0:
                    log_events.append((d, f"[LOAD] {removed} from {c['cluster_label']}"))
    
    # 4. Selesai loading
    for v_name, v_state in vessel_states.items():
        if not v_state["done"] and v_state["end_load"] == d:
            v_state["done"] = True
            log_events.append((d, f"{v_name} finished loading."))
    
    # 5. Simpan snapshot
    snapshot = []
    for slot in all_slots:
        total_in_slot = sum(slot["containers"].values())
        detail_dict = dict(slot["containers"])
        snapshot.append({
            "slot_id": slot["slot_id"],
            "total": total_in_slot,
            "detail": detail_dict
        })
    yard_snapshots[d] = snapshot

# ---------------------------------------------------------------
# 11. Static Allocation
# ---------------------------------------------------------------
# Kita buat salinan slot (tanpa timeline)
static_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        static_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "allocations": []  # list of (vessel_name, allocated_amt)
        })

# Alokasikan vessel statis (overlapping)
vessels_sorted = sorted(vessels_data, key=lambda x: x["ETA"])
for v in vessels_sorted:
    remaining = math.ceil(v["Total_Containers"])
    vessel_name = v["Vessel"]
    for slot in static_slots:
        used = sum(a[1] for a in slot["allocations"])
        free_cap = slot["capacity_per_slot"] - used
        if free_cap > 0:
            can_fill = min(free_cap, remaining)
            slot["allocations"].append((vessel_name, can_fill))
            remaining -= can_fill
        if remaining <= 0:
            break

# Buat dataframe "Slot, Vessel1, Vessel2, ..." => df_static
max_alloc = max(len(s["allocations"]) for s in static_slots)
static_table_rows = []
for s in static_slots:
    row = {"Slot": s["slot_id"]}
    for i in range(max_alloc):
        col_name = f"Vessel {i+1}"
        if i < len(s["allocations"]):
            (vname, amt) = s["allocations"][i]
            row[col_name] = f"{vname}({amt})"
        else:
            row[col_name] = ""
    static_table_rows.append(row)
df_static = pd.DataFrame(static_table_rows)

# ---------------------------------------------------------------
# 12. Fungsi Persiapan Visual
# ---------------------------------------------------------------
import altair as alt

def visualize_block_vertical(df, block_name):
    """
    Tampilkan 1 block secara vertikal:
    - sumbu Y = slot (dari atas ke bawah)
    - sumbu X = 1 kolom saja (kita pakai alt.value(0) atau dummy)
    - warna = occupant
    - tooltip menampilkan detail occupant
    """
    # Filter data untuk block yang diinginkan
    df_block = df[df["block"] == block_name].copy()
    
    # Pastikan slot bertipe int, lalu urutkan
    df_block["slot"] = df_block["slot"].astype(int)
    df_block = df_block.sort_values("slot", ascending=False)  
    # ascending=False => slot terbesar di atas atau di bawah, bisa diatur sesuai selera

    # Kita butuh kolom 'dummy_x' agar altair punya sumbu X
    df_block["dummy_x"] = 0
    
    # Buat chart
    chart = alt.Chart(df_block).mark_rect(size=20).encode(
        # X pakai nilai tetap (value(0)) atau field dummy_x
        x=alt.X('dummy_x:Q', title="", axis=None),
        y=alt.Y('slot:O', title="Slot", sort=None),
        color=alt.Color(
            'occupant:N',
            legend=alt.Legend(title="Vessel Assignments")
        ),
        tooltip=['block', 'slot', 'occupant']
    ).properties(
        width=50,       # Lebar 1 block
        height=300,     # Tinggi total block (silakan atur sesuai banyaknya slot)
        title=block_name
    )
    return chart

def visualize_blocks_side_by_side(df, blocks, title="Yard Layout"):
    """
    Buat chart gabungan (horizontal) untuk beberapa block.
    Tiap block divisualkan secara vertikal via visualize_block_vertical.
    """
    charts = []
    for blk in blocks:
        c = visualize_block_vertical(df, blk)
        charts.append(c)

    # Gabungkan secara horizontal dengan spacing
    final_chart = alt.hconcat(*charts, spacing=30).properties(title=title)
    return final_chart

# ---------------------------------------------------------------
# 13. Tampilkan di Streamlit
# ---------------------------------------------------------------
st.title("Container Yard Allocation with Static & Dynamic Visualization")

# --- Bagian 1: Dynamic
st.header("1. Dynamic Allocation (Timeline)")

df_vessels = pd.DataFrame([
    {
        "Vessel": v["Vessel"],
        "Total_Containers": v["Total_Containers"],
        "Original_ClusterNeed": v["Cluster_Need"],
        "Overriden_ClusterNeed": determine_cluster_need(v["Total_Containers"], v["Cluster_Need"]),
        "ETA": v["ETA"].strftime("%Y-%m-%d"),
        "Berth": v["Berth"]
    }
    for v in vessels_data
])
st.subheader("1.1 Data Vessels (Sorted by ETA)")
st.dataframe(df_vessels)

st.subheader("1.2 Log Events")
df_log = pd.DataFrame(log_events, columns=["Date", "Event"]).sort_values(by=["Date","Event"])
df_log.reset_index(drop=True, inplace=True)
st.dataframe(df_log)

st.subheader("1.3 Visualize Yard (Select Day)")
day_choice = st.selectbox("Choose a Day for Dynamic Snapshot", sorted(list(yard_snapshots.keys())))
chosen_snapshot = yard_snapshots[day_choice]
df_dynamic_visual = prepare_visual_dynamic(chosen_snapshot)

# Misalnya abati mau menampilkan block B03, B04, C01, C02, C03
blocks_to_show = [
    "A01", "A02", "A03", "A04", "A05",
    "B01", "B02", "B03", "B04",
    "C01", "C02", "C03"
]
chart_dynamic = visualize_multiple_blocks(df_dynamic_visual, blocks_to_show, f"Dynamic Yard - {day_choice}")
st.altair_chart(chart_dynamic, use_container_width=True)

# --- Bagian 2: Static
st.header("2. Static Allocation (Overlapping)")

st.subheader("2.1 Tabel Alokasi Static")
st.write("Setiap slot memiliki kapasitas 30 container, vessel dialokasikan berurutan sampai penuh.")
st.dataframe(df_static)

st.subheader("2.2 Visualize Static Yard")
df_static_visual = prepare_visual_static(df_static)
chart_static = visualize_multiple_blocks(df_static_visual, blocks_to_show, "Static Yard")
st.altair_chart(chart_static, use_container_width=True)

st.write("""
**Catatan**:
- Pada **Static**: Tidak ada timeline, semua kontainer dialokasikan sekaligus. 
  Jika satu slot masih sisa kapasitas, vessel berikutnya bisa mengisi.
- Pada **Dynamic**: Slot dibebaskan kembali setelah kapal selesai muat (sesuai timeline).
""")