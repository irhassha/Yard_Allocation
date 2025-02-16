import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# 1. Data Vessels (Contoh dari tabel abati)
# -------------------------------------------------------------------
vessels_data = [
    {"Vessel": "A",  "Total_Containers": 3760, "Cluster_Need": 4, "ETA_Vessel": 20240206, "Berth_Location": "NP1"},
    {"Vessel": "B",  "Total_Containers": 841.6, "Cluster_Need": 2, "ETA_Vessel": 20240206, "Berth_Location": "NP1"},
    {"Vessel": "C",  "Total_Containers": 539.2, "Cluster_Need": 2, "ETA_Vessel": 20240207, "Berth_Location": "NP1"},
    {"Vessel": "D",  "Total_Containers": 1020.8, "Cluster_Need": 3, "ETA_Vessel": 20240207, "Berth_Location": "NP1"},
    {"Vessel": "E",  "Total_Containers": 1350.4, "Cluster_Need": 4, "ETA_Vessel": 20240208, "Berth_Location": "NP1"},
    {"Vessel": "F",  "Total_Containers": 639.6, "Cluster_Need": 2, "ETA_Vessel": 20240208, "Berth_Location": "NP1"},
    {"Vessel": "G",  "Total_Containers": 1091.2, "Cluster_Need": 2, "ETA_Vessel": 20240209, "Berth_Location": "NP2"},
    {"Vessel": "H",  "Total_Containers": 1001.9, "Cluster_Need": 3, "ETA_Vessel": 20240209, "Berth_Location": "NP2"},
    {"Vessel": "I",  "Total_Containers": 1019.2, "Cluster_Need": 2, "ETA_Vessel": 20240210, "Berth_Location": "NP2"},
    {"Vessel": "J",  "Total_Containers": 983.5, "Cluster_Need": 2, "ETA_Vessel": 20240210, "Berth_Location": "NP2"},
    {"Vessel": "K",  "Total_Containers": 667.2, "Cluster_Need": 1, "ETA_Vessel": 20240211, "Berth_Location": "NP3"},
    {"Vessel": "L",  "Total_Containers": 951.7, "Cluster_Need": 2, "ETA_Vessel": 20240211, "Berth_Location": "NP3"},
    {"Vessel": "M",  "Total_Containers": 1302.4, "Cluster_Need": 2, "ETA_Vessel": 20240212, "Berth_Location": "NP1"},
    {"Vessel": "N",  "Total_Containers": 538.2, "Cluster_Need": 1, "ETA_Vessel": 20240212, "Berth_Location": "NP2"},
    {"Vessel": "O",  "Total_Containers": 1204.3, "Cluster_Need": 3, "ETA_Vessel": 20240212, "Berth_Location": "NP3"},
    {"Vessel": "P",  "Total_Containers": 1298.4, "Cluster_Need": 3, "ETA_Vessel": 20240212, "Berth_Location": "NP1"}
]

# -------------------------------------------------------------------
# 2. Info Block dan Kapasitas
#    - Tiap block punya "slots" dan "max_per_slot" = 30
#    - Total kapasitas block = slots * 30
# -------------------------------------------------------------------
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

# Kita mau bikin list "slot-level" agar mudah menempatkan vessel
# Contoh: [("A01", 1), ("A01", 2), ..., ("A01", 37), ("A02", 1), ...]
all_slots = []
for block, info in blocks_info.items():
    for slot_num in range(1, info["slots"] + 1):
        all_slots.append({
            "Block": block,
            "Slot": slot_num,
            "Capacity": info["max_per_slot"],  # Masing2 slot bisa tampung 30 kontainer
            "Vessel": None  # Nanti kita isi vessel mana
        })

# -------------------------------------------------------------------
# 3. Sort Vessel by ETA
# -------------------------------------------------------------------
vessels_data = sorted(vessels_data, key=lambda x: x["ETA_Vessel"])

# -------------------------------------------------------------------
# 4. Fungsi untuk alokasi cluster
#    - Kita ambil total kontainer, bagi ke "cluster_need"
#    - Tiap cluster kita cari slot2 kosong yang cukup menampung cluster_size
#    - Misal cluster_size = 500, itu butuh 500/30 = 16.67 => 17 slot
#      atau kita bisa isi slot satu per satu sampai habis
# -------------------------------------------------------------------
def allocate_vessel(vessel, slots_list):
    vessel_name = vessel["Vessel"]
    total = vessel["Total_Containers"]
    clusters = vessel["Cluster_Need"]

    # Bagi total ke beberapa cluster (pembagian sederhana)
    # Misal total=900, cluster=3 => 300 per cluster
    # sisanya kalo ga habis dibagi rata, kita akalin dikit
    cluster_size_base = int(total // clusters)
    remainder = int(total % clusters)

    cluster_sizes = []
    for i in range(clusters):
        size = cluster_size_base
        if i < remainder:
            size += 1
        cluster_sizes.append(size)

    results = []  # Buat nyimpen detail penempatan

    for c_idx, c_size in enumerate(cluster_sizes, start=1):
        remaining = c_size
        cluster_label = f"{vessel_name}-C{c_idx}"  # Contoh: "A-C1", "A-C2", dll.

        # Kita isi slot satu per satu
        for slot in slots_list:
            if remaining <= 0:
                break
            if slot["Vessel"] is None and slot["Capacity"] > 0:
                # Berapa container yg bisa kita taruh di slot ini?
                can_fill = min(slot["Capacity"], remaining)
                # Update slot
                slot["Capacity"] -= can_fill
                # Tandai slot ini diisi vessel (kalau mau overlap, kita butuh list. 
                # tapi contoh ini cuma 1 vessel per slot, ya)
                slot["Vessel"] = cluster_label
                remaining -= can_fill

        if remaining > 0:
            st.warning(f"⚠️ Cluster {cluster_label} tidak cukup slot! Sisa {remaining} kontainer belum teralokasi.")
        else:
            results.append((cluster_label, c_size))

    return results

# -------------------------------------------------------------------
# 5. Proses Alokasi
# -------------------------------------------------------------------
allocation_results = []
for vessel in vessels_data:
    cluster_result = allocate_vessel(vessel, all_slots)
    allocation_results.append({
        "Vessel": vessel["Vessel"],
        "Total_Containers": vessel["Total_Containers"],
        "Cluster_Need": vessel["Cluster_Need"],
        "ETA_Vessel": vessel["ETA_Vessel"],
        "Assigned_Clusters": cluster_result
    })

# -------------------------------------------------------------------
# 6. Tampilkan di Streamlit
# -------------------------------------------------------------------
st.title("Container Yard Allocation Demo")
st.write("Halo abati, ini contoh simpel alokasi yard per slot.")

st.subheader("1. Data Vessels (Sorted by ETA)")
df_vessels = pd.DataFrame(vessels_data)
st.dataframe(df_vessels)

st.subheader("2. Hasil Allocation per Vessel")
for res in allocation_results:
    st.write(f"**Vessel {res['Vessel']}** (Total: {res['Total_Containers']}, "
             f"ClusterNeed: {res['Cluster_Need']}, ETA: {res['ETA_Vessel']})")
    if res["Assigned_Clusters"]:
        for (cluster_label, csize) in res["Assigned_Clusters"]:
            st.write(f"- {cluster_label} = {csize} kontainer")
    else:
        st.write("- Tidak teralokasi!")

st.subheader("3. Alokasi Slot (Final)")
# Kita mau tampilin table: Slot, Vessel1, Vessel2, ...
# Tapi contoh ini "1 slot" cuma menampung 1 cluster_label (nggak overlap).
# Kita bikin dataframe yang menampilkan (Block, Slot, Vessel) aja.

df_slots = pd.DataFrame(all_slots)
# Buat keperluan tampilan, kita gabungin "Block-Slot" jadi satu kolom
df_slots["Block_Slot"] = df_slots["Block"] + "-" + df_slots["Slot"].astype(str)
df_display = df_slots[["Block_Slot", "Vessel", "Capacity"]].copy()
st.dataframe(df_display)

st.write("""
**Catatan**:
- `Capacity` menunjukkan sisa slot (dari 30) setelah dialokasikan. 
- `Vessel` diisi dengan "VesselName-ClusterIndex" (misal: A-C1).
- Kalau ada sisa container yang nggak teralokasi, akan muncul warning di atas.
- Ini masih contoh sederhana, belum ada logika overlap day-by-day, dll.
""")
