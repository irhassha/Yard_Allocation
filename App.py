import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta

# ---------------------------------------------------------------
# 1. Data Awal
#    Silakan isi sesuai data abati. "Cluster_Need" bisa di-override
#    oleh aturan <1000 => 3, <1500 => 2 di bawah.
# ---------------------------------------------------------------
vessels_data = [
    {"Vessel": "A", "Total_Containers": 3760, "Cluster_Need": 4, "ETA": date(2024,2,6), "Berth": "NP1"},
    {"Vessel": "B", "Total_Containers": 842,  "Cluster_Need": 2, "ETA": date(2024,2,6), "Berth": "NP1"},
    {"Vessel": "C", "Total_Containers": 539,  "Cluster_Need": 2, "ETA": date(2024,2,7), "Berth": "NP1"},
    {"Vessel": "D", "Total_Containers": 1021, "Cluster_Need": 3, "ETA": date(2024,2,7), "Berth": "NP1"},
    {"Vessel": "E", "Total_Containers": 1350, "Cluster_Need": 4, "ETA": date(2024,2,8), "Berth": "NP1"},
    {"Vessel": "F", "Total_Containers": 639,  "Cluster_Need": 2, "ETA": date(2024,2,8), "Berth": "NP1"},
    {"Vessel": "G", "Total_Containers": 1091, "Cluster_Need": 2, "ETA": date(2024,2,9), "Berth": "NP2"},
    {"Vessel": "H", "Total_Containers": 1002, "Cluster_Need": 3, "ETA": date(2024,2,9), "Berth": "NP2"},
    {"Vessel": "I", "Total_Containers": 1019, "Cluster_Need": 2, "ETA": date(2024,2,10), "Berth": "NP2"},
    {"Vessel": "J", "Total_Containers": 983,  "Cluster_Need": 2, "ETA": date(2024,2,10), "Berth": "NP2"},
    {"Vessel": "K", "Total_Containers": 667,  "Cluster_Need": 1, "ETA": date(2024,2,11), "Berth": "NP3"},
    {"Vessel": "L", "Total_Containers": 952,  "Cluster_Need": 2, "ETA": date(2024,2,11), "Berth": "NP3"},
    {"Vessel": "M", "Total_Containers": 1302, "Cluster_Need": 2, "ETA": date(2024,2,12), "Berth": "NP1"},
    {"Vessel": "N", "Total_Containers": 538,  "Cluster_Need": 1, "ETA": date(2024,2,12), "Berth": "NP2"},
    {"Vessel": "O", "Total_Containers": 1204, "Cluster_Need": 3, "ETA": date(2024,2,12), "Berth": "NP3"},
    {"Vessel": "P", "Total_Containers": 1298, "Cluster_Need": 3, "ETA": date(2024,2,12), "Berth": "NP1"},
]

# ---------------------------------------------------------------
# 2. Info Block & Preferensi
#    - Tiap block punya kapasitas (slots × 30 kontainer/slot).
#    - Kita definisikan preferensi block per Berth:
#      NP1 -> A-block, B-block, C-block
#      NP2 -> B-block, A-block, C-block
#      NP3 -> C-block, B-block, A-block
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
        return ["A", "B", "C"]  # default

# ---------------------------------------------------------------
# 3. Membuat struktur all_slots
#    Di setiap slot, kita simpan 'containers' -> dict { cluster_label: jumlah }
#    agar memungkinkan multi cluster di satu slot.
# ---------------------------------------------------------------
all_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"]+1):
        slot_id = f"{block}-{s}"
        all_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "containers": {}  # cluster_label -> qty
        })

# Kita juga butuh cara cepat untuk filter slot per prefix
def block_prefix(slot_id):
    """Balikin prefix 'A', 'B', atau 'C' dari slot_id, mis: 'A01-3' -> 'A'."""
    return slot_id[0]  # Asumsi format block: A01, B02, dsb.

# ---------------------------------------------------------------
# 4. Aturan Minimal Cluster
# ---------------------------------------------------------------
def determine_cluster_need(total_from_data, cluster_from_data):
    """Jika total <1000 => 3 cluster,
       elif total <1500 => 2 cluster,
       else => pakai cluster_from_data."""
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
    move_per_day = CRANE_MOVE_PER_HOUR * CRANE_COUNT * 24  # mis: 75.6 * 24 = 1814.4
    days = total_containers / move_per_day
    return math.ceil(days)

# ---------------------------------------------------------------
# 6. Buat timeline (day-by-day)
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
# 7. Siapkan vessel_states untuk track jadwal, cluster, dsb.
# ---------------------------------------------------------------
vessel_states = {}
for v in vessels_data:
    v_name = v["Vessel"]
    total_c = math.ceil(v["Total_Containers"])
    # override cluster jika perlu
    needed_cluster = determine_cluster_need(total_c, v["Cluster_Need"])
    
    # Bagi cluster
    base_csize = total_c // needed_cluster
    rem = total_c % needed_cluster
    clusters = []
    for i in range(needed_cluster):
        size_ = base_csize + (1 if i < rem else 0)
        clusters.append({
            "cluster_label": f"{v_name}-C{i+1}",
            "size": size_,
            "remain": size_,  # sisa belum 'datang' + belum 'termuat'
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
# 8. Hindari Clash ETA < 3 Hari
#    Kita simpan "block_in_use" per vessel (ketika vessel menaruh container).
#    Sebelum menaruh cluster baru, kita cek ETA vessel lain di block tsb.
# ---------------------------------------------------------------
# Kita butuh dictionary: block_usage[block] = list of (vessel_name, ETA)
block_usage = {}

def is_clashing(this_vessel, block, states, margin_days=3):
    """Cek apakah menempatkan 'this_vessel' ke block akan clash
       dengan vessel lain di block yang ETA-nya beda < 3 hari."""
    if block not in block_usage:
        return False
    
    this_eta = states[this_vessel]["ETA"]
    for (other_vessel, other_eta) in block_usage[block]:
        diff = abs((this_eta - other_eta).days)
        if diff < margin_days:
            # clash
            return True
    return False

def mark_block_usage(vessel, block):
    """Tandai block digunakan oleh vessel ini."""
    v_eta = vessel_states[vessel]["ETA"]
    if block not in block_usage:
        block_usage[block] = []
    block_usage[block].append((vessel, v_eta))

# ---------------------------------------------------------------
# 9. Fungsi Alokasi Container (Day-by-Day) dengan Preferensi Block
#    - Kita coba block prefix sesuai berth order.
#    - Cek clash, kalau clash skip block prefix itu.
#    - Kalau tidak clash, isi slot di block itu sampai habis atau cluster habis.
# ---------------------------------------------------------------
def allocate_with_preference(cluster_label, qty, vessel_name):
    """Menaruh 'qty' kontainer ke block-block sesuai preferensi,
       hindari block yang clash. Kembalikan sisa yang tidak teralokasi."""
    berth = vessel_states[vessel_name]["Berth"]
    prefix_order = get_block_prefix_order(berth)  # e.g. ["A","B","C"]
    remaining = qty
    
    # Kita akan loop prefix (A/B/C), lalu cari slot yang prefix-nya sama.
    # Per block, kita cek "clash" dengan ETA < 3 hari. 
    # Kalau clash, skip block itu. 
    # (Implementasi minimal: skip semua block Axx kalau clash.)
    
    for pfx in prefix_order:
        if remaining <= 0:
            break
        # Kumpulkan slot-slot berprefix pfx
        # Lalu group by block name: A01, A02, dsb.
        block_slots_map = {}
        for slot in all_slots:
            if slot["block"].startswith(pfx):
                block_slots_map.setdefault(slot["block"], []).append(slot)
        
        # Sort block by name (A01, A02, ...)
        for block_name in sorted(block_slots_map.keys()):
            if remaining <= 0:
                break
            # cek clash
            if is_clashing(vessel_name, block_name, vessel_states):
                # kalau clash, skip block ini
                continue
            
            # kalau tidak clash, kita isi slot-slot di block ini
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
            
            # kalau kita berhasil menaruh sesuatu di block_name,
            # tandai block_usage
            if remaining < qty:  # artinya kita taruh minimal 1 container
                mark_block_usage(vessel_name, block_name)
                
        # lanjut ke prefix berikutnya kalau masih sisa

    return remaining

# ---------------------------------------------------------------
# 10. Fungsi Remove Container (Loading)
# ---------------------------------------------------------------
def remove_cluster_containers(cluster_label, qty):
    """Mengurangi 'qty' kontainer cluster_label dari yard."""
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
# 11. Simulasi Day-by-Day
# ---------------------------------------------------------------
log_events = []

for d in all_days:
    # 1. Tandai kapal yang loading sudah lewat end_load => done
    for v_name, st in vessel_states.items():
        if not st["done"] and d > st["end_load"]:
            st["done"] = True
    
    # 2. Receiving
    for v_name, st in vessel_states.items():
        if st["done"]:
            continue
        if st["start_receive"] <= d <= st["end_receive"]:
            # ~12% per hari
            daily_in = math.ceil(st["Total"] * RECEIVING_RATE)
            # Bagi ke cluster
            for c in st["Clusters"]:
                if c["remain"] > 0:
                    # portion daily_in * (c.size / total)
                    portion = math.ceil(daily_in * (c["size"] / st["Total"]))
                    portion = min(portion, c["remain"])
                    if portion > 0:
                        leftover = allocate_with_preference(c["cluster_label"], portion, v_name)
                        allocated = portion - leftover
                        c["remain"] -= allocated
                        if allocated > 0:
                            log_events.append((d, f"[RECV] {allocated} to {c['cluster_label']}"))
        elif d == st["ETA"]:
            # Sisa remain
            for c in st["Clusters"]:
                if c["remain"] > 0:
                    leftover = allocate_with_preference(c["cluster_label"], c["remain"], v_name)
                    allocated = c["remain"] - leftover
                    c["remain"] -= allocated
                    if allocated > 0:
                        log_events.append((d, f"[RECV-FINAL] {allocated} to {c['cluster_label']}"))
    
    # 3. Loading
    for v_name, st in vessel_states.items():
        if st["done"]:
            continue
        if st["start_load"] <= d <= st["end_load"]:
            # total day loading
            ld = get_loading_days(st["Total"])
            daily_out = math.ceil(st["Total"] / ld)
            for c in st["Clusters"]:
                c_size = c["size"]
                portion_out = math.ceil(daily_out * (c_size / st["Total"]))
                # remove
                leftover_remove = remove_cluster_containers(c["cluster_label"], portion_out)
                removed = portion_out - leftover_remove
                if removed > 0:
                    log_events.append((d, f"[LOAD] {removed} from {c['cluster_label']}"))
    
    # 4. Cek kapal yang end_load == d => done
    for v_name, st in vessel_states.items():
        if not st["done"] and st["end_load"] == d:
            st["done"] = True
            log_events.append((d, f"{v_name} finished loading."))

# ---------------------------------------------------------------
# 12. Tampilkan di Streamlit
# ---------------------------------------------------------------
st.title("Dynamic Yard Allocation (Timeline) - Advanced Example")
st.write("""
**Fitur**:
1. Minimal cluster: <1000 => 3, <1500 => 2, sisanya pakai data.
2. Preferensi block: 
   - NP1 => A -> B -> C  
   - NP2 => B -> A -> C  
   - NP3 => C -> B -> A  
3. Hindari clash ETA < 3 hari di block yang sama.
4. Timeline day-by-day: receiving ±12%/hari (7 hari), loading => slot dibebaskan.

Lihat 'Log Events' untuk kronologi receiving/loading, 
serta 'Final Yard Usage' untuk kondisi akhir slot.
""")

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

df_log = pd.DataFrame(log_events, columns=["Date", "Event"])
df_log.sort_values(by=["Date","Event"], inplace=True)
df_log.reset_index(drop=True, inplace=True)
st.subheader("2. Log Events")
st.dataframe(df_log)

st.subheader("3. Final Yard Usage")
slot_rows = []
for s in all_slots:
    total_in_slot = sum(s["containers"].values())
    if total_in_slot > 0:
        detail = ", ".join(f"{k}({v})" for k,v in s["containers"].items())
    else:
        detail = ""
    slot_rows.append({
        "Slot_ID": s["slot_id"],
        "Total_Used": total_in_slot,
        "Detail": detail
    })
df_slots = pd.DataFrame(slot_rows)
st.dataframe(df_slots[df_slots["Total_Used"]>0].reset_index(drop=True))

st.write("""
**Catatan**:
- Kalau banyak slot kosong di akhir, artinya kapal2 sudah selesai muat.
- Jika masih ada kontainer di slot, berarti kapal tsb belum selesai di hari terakhir timeline (atau perlu penyesuaian).
- Mekanisme 'hindari clash' di sini sangat sederhana: 
  jika block pernah dipakai oleh kapal X (ETA_X), 
  maka kapal lain dengan |ETA - ETA_X| < 3 hari akan skip block tsb.
""")