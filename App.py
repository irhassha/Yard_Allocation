import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta

# ---------------------------------------------------------------------
# 1. Data Awal
# ---------------------------------------------------------------------
vessels_data = [
    # Contoh data (silakan sesuaikan)
    {"Vessel": "A", "Total_Containers": 3760, "Cluster_Need": 4, "ETA": date(2024,2,6), "Berth": "NP1"},
    {"Vessel": "B", "Total_Containers": 842,  "Cluster_Need": 2, "ETA": date(2024,2,6), "Berth": "NP1"},
    {"Vessel": "C", "Total_Containers": 539,  "Cluster_Need": 2, "ETA": date(2024,2,7), "Berth": "NP1"},
    {"Vessel": "D", "Total_Containers": 1021, "Cluster_Need": 3, "ETA": date(2024,2,7), "Berth": "NP1"},
    # ... dan seterusnya
]

# Info block
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

# ---------------------------------------------------------------------
# 2. Siapkan Struktur Yard
#    Kita akan menyimpan data "slot usage" day-by-day.
# ---------------------------------------------------------------------
# Buat list slot
all_slots = []
for block, info in blocks_info.items():
    for s in range(1, info["slots"] + 1):
        slot_id = f"{block}-{s}"
        # Kita simpan data usage dalam dict:
        # "containers": {vessel_name: jumlah_kontainer} 
        # agar 1 slot bisa menampung multi vessel (kalau masih ada kapasitas).
        all_slots.append({
            "slot_id": slot_id,
            "block": block,
            "capacity_per_slot": info["max_per_slot"],
            "containers": {}  # "Vessel-Cluster" -> jumlah
        })

# ---------------------------------------------------------------------
# 3. Parameter Operasional
# ---------------------------------------------------------------------
RECEIVING_DAYS = 7
RECEIVING_RATE = 0.12   # 12% per hari x 7 = 84%, sisanya 16% di hari ETA
CRANE_MOVE_PER_HOUR = 28
CRANE_COUNT = 2.7

# Buat helper untuk hitung durasi loading (dalam hari)
def get_loading_days(total_containers):
    # misal 28 move/jam * 2.7 crane = 75.6 move/jam
    # 1 hari = 24 jam => 75.6 * 24 = 1814.4 move/hari
    move_per_day = CRANE_MOVE_PER_HOUR * CRANE_COUNT * 24
    days = total_containers / move_per_day
    return math.ceil(days)  # bulatkan ke atas

# ---------------------------------------------------------------------
# 4. Tentukan timeline (rentang hari)
# ---------------------------------------------------------------------
min_eta = min(v["ETA"] for v in vessels_data)
max_eta = max(v["ETA"] for v in vessels_data)

start_date = min_eta - timedelta(days=RECEIVING_DAYS)
end_date = max_eta + timedelta(days=30)  # tambahkan 30 hari cadangan utk loading

# Generate list of all days
all_days = []
current_day = start_date
while current_day <= end_date:
    all_days.append(current_day)
    current_day += timedelta(days=1)

# ---------------------------------------------------------------------
# 5. Siapkan struktur untuk tracking Vessel State
#    - Kapan start receiving, end receiving
#    - Kapan start loading, end loading
#    - Berapa container yg sudah ada di yard, berapa sisa
# ---------------------------------------------------------------------
vessel_states = {}
for v in vessels_data:
    v_name = v["Vessel"]
    total_c = math.ceil(v["Total_Containers"])
    eta = v["ETA"]
    cluster_need = v["Cluster_Need"]
    
    # Bagi total kontainer jadi cluster2 (simple)
    base_cluster = total_c // cluster_need
    remainder = total_c % cluster_need
    clusters = []
    for i in range(cluster_need):
        csize = base_cluster + (1 if i < remainder else 0)
        clusters.append({
            "cluster_label": f"{v_name}-C{i+1}",
            "size": csize,
            "remain": csize,  # sisa kontainer belum dimuat
        })
    
    # Receiving window: [ETA - 7, ETA-1], setiap hari ~12%, sisanya 16% di ETA
    start_receive = eta - timedelta(days=RECEIVING_DAYS)
    end_receive = eta - timedelta(days=1)
    
    # Loading duration
    load_days = get_loading_days(total_c)
    start_load = eta  # asumsikan mulai loading di hari ETA
    end_load = eta + timedelta(days=load_days - 1)  # -1 karena start_load termasuk
    
    vessel_states[v_name] = {
        "Vessel": v_name,
        "Total": total_c,
        "Clusters": clusters,
        "ETA": eta,
        "start_receive": start_receive,
        "end_receive": end_receive,
        "start_load": start_load,
        "end_load": end_load,
        "done": False,  # apakah sudah selesai muat
    }

# ---------------------------------------------------------------------
# 6. Fungsi alokasi container ke yard (1 cluster per kali panggil)
# ---------------------------------------------------------------------
def allocate_containers_to_yard(cluster_label, qty, slots_list):
    """Mencoba menaruh 'qty' kontainer dari cluster_label ke yard.
       Return: sisa yang tidak teralokasi."""
    remaining = qty
    for slot in slots_list:
        if remaining <= 0:
            break
        # Hitung kapasitas slot yang tersisa
        used = sum(slot["containers"].values())  # total kontainer di slot
        free_capacity = slot["capacity_per_slot"] - used
        if free_capacity > 0:
            can_fill = min(free_capacity, remaining)
            slot["containers"].setdefault(cluster_label, 0)
            slot["containers"][cluster_label] += can_fill
            remaining -= can_fill
    return remaining

# ---------------------------------------------------------------------
# 7. Fungsi untuk loading (mengeluarkan kontainer dari yard)
# ---------------------------------------------------------------------
def remove_containers_from_yard(cluster_label, qty, slots_list):
    """Mengurangi 'qty' kontainer milik cluster_label dari yard."""
    remaining = qty
    for slot in slots_list:
        if remaining <= 0:
            break
        if cluster_label in slot["containers"]:
            available_here = slot["containers"][cluster_label]
            take = min(available_here, remaining)
            slot["containers"][cluster_label] -= take
            remaining -= take
            # kalau sudah 0, hapus key-nya
            if slot["containers"][cluster_label] <= 0:
                del slot["containers"][cluster_label]
    return remaining

# ---------------------------------------------------------------------
# 8. Simulasi Day-by-Day
# ---------------------------------------------------------------------
log_events = []  # buat nyimpan catatan event harian

for d in all_days:
    # 1. Cek kapal mana yang loading selesai hari kemarin, tandai done (opsional)
    #    (Di sini kita cek kalau d > end_load, berarti loading kemarin sudah final)
    for v_name, stt in vessel_states.items():
        if not stt["done"] and d > stt["end_load"]:
            # Kapal ini sudah lewat masa loading
            stt["done"] = True
    
    # 2. Terima kontainer (receiving)
    #    Jika d di antara start_receive dan end_receive, maka ~12% / day
    #    Jika d == ETA, maka sisanya 16%
    for v_name, stt in vessel_states.items():
        if stt["done"]:
            continue
        if stt["start_receive"] <= d <= stt["end_receive"]:
            # 12% of total / day
            daily_in = int(math.ceil(stt["Total"] * RECEIVING_RATE))
            # Bagi per cluster
            for c in stt["Clusters"]:
                # csize -> total cluster
                # c["remain"] -> sisa cluster yang belum "datang" ke yard
                if c["size"] <= 0:
                    continue
                # asumsikan daily_in dibagi proporsional
                # (sederhana: daily_in * (c.size / stt["Total"]))
                portion = int(math.ceil(daily_in * (c["size"]/stt["Total"])))
                portion = min(portion, c["remain"])  # jgn melebihi sisa
                if portion > 0:
                    leftover = allocate_containers_to_yard(c["cluster_label"], portion, all_slots)
                    allocated = portion - leftover
                    c["remain"] -= allocated
                    if allocated > 0:
                        log_events.append((d, f"Receive {allocated} for {c['cluster_label']}"))
                    
        elif d == stt["ETA"]:
            # sisanya 16% (kalo masih ada remain di cluster)
            # tapi kita ambil "sisa remain" aja. 
            # 16% itu perkiraan, tapi di day-by-day real, kita cukup ambil c["remain"].
            for c in stt["Clusters"]:
                if c["remain"] > 0:
                    leftover = allocate_containers_to_yard(c["cluster_label"], c["remain"], all_slots)
                    allocated = c["remain"] - leftover
                    c["remain"] -= allocated
                    if allocated > 0:
                        log_events.append((d, f"Final receive {allocated} for {c['cluster_label']}"))

    # 3. Loading
    #    Jika d di rentang [start_load, end_load], berarti kapal loading.
    #    Kita tentukan berapa kontainer di-load per hari.
    for v_name, stt in vessel_states.items():
        if stt["done"]:
            continue
        if stt["start_load"] <= d <= stt["end_load"]:
            # total kontainer = stt["Total"]
            # total loading days = get_loading_days(stt["Total"])
            ld = get_loading_days(stt["Total"])
            daily_out = math.ceil(stt["Total"] / ld)  # kurang lebih
            # Bagi ke cluster
            # per cluster: cluster_size / total_size -> porsi
            # Lalu remove di yard
            for c in stt["Clusters"]:
                c_size = c["size"]
                portion_out = math.ceil(daily_out * (c_size / stt["Total"]))
                # cek brp beneran masih ada di yard?
                # Sebenernya kita harus cari total di yard, tapi kita coba remove aja
                leftover_remove = remove_containers_from_yard(c["cluster_label"], portion_out, all_slots)
                removed = portion_out - leftover_remove
                if removed > 0:
                    log_events.append((d, f"Load {removed} from {c['cluster_label']}"))
    
    # 4. Di akhir hari, cek apakah kapal yang end_load == d sudah rampung
    for v_name, stt in vessel_states.items():
        if not stt["done"] and stt["end_load"] == d:
            # artinya di hari ini loading berakhir
            stt["done"] = True
            log_events.append((d, f"{v_name} finished loading."))

# ---------------------------------------------------------------------
# 9. Tampilkan di Streamlit
# ---------------------------------------------------------------------
st.title("Dynamic Yard Allocation (Timeline Approach)")
st.write("""
Contoh sederhana pendekatan timeline (day-by-day).  
- Setiap hari kita **terima** kontainer (jika masih dalam window receiving).  
- Setiap hari kita **muat** (jika sudah dalam window loading).  
- Begitu kapal selesai, slot di yard otomatis kosong (bisa dipakai kapal lain).  
""")

st.subheader("Data Vessel")
df_vessel_init = pd.DataFrame([
    {
        "Vessel": v["Vessel"],
        "Total_Containers": v["Total_Containers"],
        "Cluster_Need": v["Cluster_Need"],
        "ETA": v["ETA"],
        "start_receive": (v["ETA"] - timedelta(days=RECEIVING_DAYS)).strftime("%Y-%m-%d"),
        "end_receive": (v["ETA"] - timedelta(days=1)).strftime("%Y-%m-%d"),
        "start_load": v["ETA"].strftime("%Y-%m-%d"),
        "end_load": (v["ETA"] + timedelta(days=get_loading_days(v["Total_Containers"])-1)).strftime("%Y-%m-%d"),
    }
    for v in vessels_data
])
st.dataframe(df_vessel_init)

st.subheader("Log Events (Chronological)")
df_log = pd.DataFrame(log_events, columns=["Date", "Event"])
df_log = df_log.sort_values(by=["Date","Event"]).reset_index(drop=True)
st.dataframe(df_log)

st.subheader("Final Yard Usage (Terakhir)")
# Setelah semua hari selesai, kita lihat sisa container di slot
slot_rows = []
for s in all_slots:
    total_in_slot = sum(s["containers"].values())
    # list cluster: "A-C1(10), B-C2(20)"
    cluster_list = []
    for cl, qty in s["containers"].items():
        cluster_list.append(f"{cl}({qty})")
    slot_rows.append({
        "Slot_ID": s["slot_id"],
        "Total_Used": total_in_slot,
        "Detail": ", ".join(cluster_list)
    })

df_slots_final = pd.DataFrame(slot_rows)
st.dataframe(df_slots_final)

st.write("""
**Keterangan**:
- Kalau simulasi ini berjalan lancar, banyak slot akan kosong di akhir (Total_Used=0) karena kapal2 sudah selesai muat.
- Kalau ada kapal yang masih proses, sisa kontainernya akan tampak di kolom 'Detail'.
- Pendekatan ini masih kasar (day-by-day, pembagian daily_in/daily_out simplistik). 
  Untuk hasil lebih akurat, bisa ditingkatkan ke level jam dan menambahkan logika prioritas, dll.
""")