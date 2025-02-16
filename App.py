import streamlit as st
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
    """Return urutan block prefix (A, B, C) sesuai berth."""
    if berth == "NP1":
        return ["A", "B", "C"]
    elif berth == "NP2":
        return ["B", "A", "C"]
    elif berth == "NP3":
        return ["C", "B", "A"]
    else:
        return ["A", "B", "C"]

# ---------------------------------------------------------------
# 3. Membuat struktur all_slots (untuk simulasi dinamis)
# ---------------------------------------------------------------
all_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        all_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "containers": {}  # cluster_label -> qty (dipakai pada simulasi dinamis)
        })

# ---------------------------------------------------------------
# 4. Aturan Minimal Cluster
# ---------------------------------------------------------------
def determine_cluster_need(total_from_data, cluster_from_data):
    """
    Jika total <1000 => 3 cluster,
    elif total <1500 => 2 cluster,
    else => pakai cluster_from_data.
    """
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
    """Hitung durasi loading (hari) berdasarkan kapasitas crane."""
    move_per_day = CRANE_MOVE_PER_HOUR * CRANE_COUNT * 24
    days = total_containers / move_per_day
    return math.ceil(days)

# ---------------------------------------------------------------
# 6. Buat timeline (day-by-day) untuk simulasi dinamis
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
# 7. Siapkan vessel_states untuk simulasi dinamis
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
            "remain": size_,  # sisa yang belum dialokasikan/termuat
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
# 8. Hindari Clash ETA < 3 Hari (simulasi dinamis)
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
# 9. Fungsi Alokasi Dinamis dengan Preferensi Block + Clash Check
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

# ---------------------------------------------------------------
# 10. Fungsi Remove Container (Loading) untuk simulasi dinamis
# ---------------------------------------------------------------
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
# 11. Simulasi Dinamis Day-by-Day + Snapshot Yard
# ---------------------------------------------------------------
yard_snapshots = {}  # key: date, value: snapshot (list of slot usage)
log_events = []

for d in all_days:
    # Tandai kapal yang sudah selesai loading (jika d > end_load)
    for vessel_name, v_state in vessel_states.items():
        if not v_state["done"] and d > v_state["end_load"]:
            v_state["done"] = True
    # Receiving
    for vessel_name, v_state in vessel_states.items():
        if v_state["done"]:
            continue
        if v_state["start_receive"] <= d <= v_state["end_receive"]:
            daily_in = math.ceil(v_state["Total"] * RECEIVING_RATE)
            for cluster in v_state["Clusters"]:
                if cluster["remain"] > 0:
                    portion = math.ceil(daily_in * (cluster["size"] / v_state["Total"]))
                    portion = min(portion, cluster["remain"])
                    if portion > 0:
                        leftover = allocate_with_preference(cluster["cluster_label"], portion, vessel_name)
                        allocated = portion - leftover
                        cluster["remain"] -= allocated
                        if allocated > 0:
                            log_events.append((d, f"[RECV] {allocated} to {cluster['cluster_label']}"))
        elif d == v_state["ETA"]:
            for cluster in v_state["Clusters"]:
                if cluster["remain"] > 0:
                    leftover = allocate_with_preference(cluster["cluster_label"], cluster["remain"], vessel_name)
                    allocated = cluster["remain"] - leftover
                    cluster["remain"] -= allocated
                    if allocated > 0:
                        log_events.append((d, f"[RECV-FINAL] {allocated} to {cluster['cluster_label']}"))
    # Loading
    for vessel_name, v_state in vessel_states.items():
        if v_state["done"]:
            continue
        if v_state["start_load"] <= d <= v_state["end_load"]:
            ld = get_loading_days(v_state["Total"])
            daily_out = math.ceil(v_state["Total"] / ld)
            for cluster in v_state["Clusters"]:
                portion_out = math.ceil(daily_out * (cluster["size"] / v_state["Total"]))
                leftover_remove = remove_cluster_containers(cluster["cluster_label"], portion_out)
                removed = portion_out - leftover_remove
                if removed > 0:
                    log_events.append((d, f"[LOAD] {removed} from {cluster['cluster_label']}"))
    # Tandai selesai loading jika d == end_load
    for vessel_name, v_state in vessel_states.items():
        if not v_state["done"] and v_state["end_load"] == d:
            v_state["done"] = True
            log_events.append((d, f"{vessel_name} finished loading."))
    # Simpan snapshot yard di akhir hari d
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
# 12. Tampilan Dynamic Allocation di Streamlit
# ---------------------------------------------------------------
st.title("Dynamic Yard Allocation (Timeline) - Advanced with Daily Snapshots")
st.write("""
**Fitur Dynamic:**
1. Minimal cluster: <1000 => 3, <1500 => 2, sisanya pakai data.
2. Preferensi block: NP1 ⇒ A → B → C, NP2 ⇒ B → A → C, NP3 ⇒ C → B → A.
3. Hindari clash ETA < 3 hari di block yang sama.
4. Timeline day-by-day: receiving ±12%/hari (7 hari), loading → slot dibebaskan.
5. Snapshot harian: pilih tanggal untuk lihat kondisi yard.
""")

# 12.1 Tampilkan Data Vessels
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
st.subheader("1. Data Vessels")
st.dataframe(df_vessels)

# 12.2 Tampilkan Log Events
df_log = pd.DataFrame(log_events, columns=["Date", "Event"])
df_log.sort_values(by=["Date", "Event"], inplace=True)
df_log.reset_index(drop=True, inplace=True)
st.subheader("2. Log Events (Chronological)")
st.dataframe(df_log)

# 12.3 Pilih Hari untuk Snapshot Yard
st.subheader("3. Snapshot Yard (Dynamic)")
day_choice = st.selectbox("Pilih Tanggal", sorted(list(yard_snapshots.keys())))
chosen_snapshot = yard_snapshots[day_choice]
rows = []
for s in chosen_snapshot:
    if s["total"] > 0:
        detail_str = ", ".join(f"{k}({v})" for k, v in s["detail"].items())
    else:
        detail_str = ""
    rows.append({
        "Slot_ID": s["slot_id"],
        "Total_Used": s["total"],
        "Detail": detail_str
    })
df_chosen = pd.DataFrame(rows)
st.dataframe(df_chosen[df_chosen["Total_Used"] > 0].reset_index(drop=True))

st.write("""
**Catatan Dynamic:**
- Jika "Total_Used" kosong di suatu hari, artinya yard sedang kosong.
- Di akhir timeline, kemungkinan yard sudah kosong karena semua kapal selesai muat.
""")

# ---------------------------------------------------------------
# 13. Static Allocation (Overlapping Method)
# ---------------------------------------------------------------
# Kita buat salinan baru static_slots (tanpa simulasi timeline)
static_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        static_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "allocations": []  # list of (vessel_name, allocated_amount)
        })

# Algoritma Static Allocation: untuk tiap vessel, alokasikan seluruh container ke slot yang tersedia.
vessels_sorted = sorted(vessels_data, key=lambda x: x["ETA"])
for v in vessels_sorted:
    remaining = math.ceil(v["Total_Containers"])
    vessel_name = v["Vessel"]
    for slot in static_slots:
        # Hitung kapasitas tersisa di slot
        used = sum(alloc[1] for alloc in slot["allocations"])
        free_cap = slot["capacity_per_slot"] - used
        if free_cap > 0:
            allocate_amt = min(free_cap, remaining)
            slot["allocations"].append((vessel_name, allocate_amt))
            remaining -= allocate_amt
        if remaining <= 0:
            break

# Buat tabel static allocation: kolom "Slot", "Vessel 1", "Vessel 2", dst.
max_allocations = max(len(slot["allocations"]) for slot in static_slots)
static_table_rows = []
for slot in static_slots:
    row = {"Slot": slot["slot_id"]}
    for i in range(max_allocations):
        col_name = f"Vessel {i+1}"
        if i < len(slot["allocations"]):
            vessel_alloc, amt = slot["allocations"][i]
            row[col_name] = f"{vessel_alloc}({amt})"
        else:
            row[col_name] = ""
    static_table_rows.append(row)
df_static = pd.DataFrame(static_table_rows)

# ---------------------------------------------------------------
# 14. Tampilkan Static Allocation Table di Streamlit
# ---------------------------------------------------------------
st.subheader("Static Allocation Table (Overlapping)")
st.write("""
Tabel ini mengalokasikan seluruh container secara statis menggunakan metode overlapping (misalnya, satu slot bisa berisi Vessel 1 dan Vessel 2).
""")
st.dataframe(df_static)

st.write("""
**Catatan Static:**
- Pada tabel ini, setiap slot memiliki kapasitas 30 container.
- Jika suatu slot tidak penuh, vessel berikutnya dapat mengisi sisa kapasitas tersebut.
- Tabel ini tidak memperhitungkan timeline; seluruh vessel dialokasikan secara statis.
""")