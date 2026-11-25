import pandas as pd

TANGGAL = "2026-11-25"

# source_id OpenAlex: (kategori, bahasa)
PILIH = {
    "W7143582459": ("Keamanan Siber", "id"),   # Matematika Kriptografi Kontemporer
    "W7213385684": ("Keamanan Siber", "id"),   # Modernisasi Keamanan Akses Infrastruktur TI
    "W7171904128": ("Keamanan Siber", "id"),   # Routing Aman dengan MANRS
    "W3085062564": ("Keamanan Siber", "id"),   # Kriptografi: Teknik Keamanan Data dan Informasi
}

k = pd.read_csv("data/kandidat_openalex.csv")
d = pd.read_csv("data/dataset.csv")

mulai = int(d.doc_id.str[3:].max()) + 1
baris = []
for i, (sid, (kategori, bahasa)) in enumerate(PILIH.items()):
    cocok = k[k.source_id == sid]
    assert len(cocok) == 1, f"{sid} tidak ditemukan di kandidat"
    r = cocok.iloc[0]
    baris.append({
        "doc_id": f"DOC{mulai + i:03d}", "title": r.title, "author": r.author, "year": r.year,
        "category": kategori, "language": bahasa, "source": "openalex_api", "source_id": sid,
        "source_url": r.source_url, "retrieved_at": TANGGAL, "content": f"{r.title}. {r.abstrak}",
    })

b = pd.DataFrame(baris)[list(d.columns)]
d["year"] = d["year"].astype("Int64")
b["year"] = b["year"].astype("Int64")

assert TANGGAL != "ISI-TANGGAL-PENGAMBILAN", "Isi tanggal pengambilan dulu"
assert not set(d.doc_id) & set(b.doc_id), "doc_id bentrok"
assert not set(d.source_id) & set(b.source_id), "source_id sudah ada di dataset"
assert set(b.category) <= set(d.category), "ejaan kategori tidak cocok"
assert (b.content.str.split().str.len() >= 30).all(), "ada dokumen kurang dari 30 kata"

pd.concat([d, b]).to_csv("data/dataset.csv", index=False, encoding="utf-8")
print("Selesai. Total dokumen:", len(d) + len(b))
print(pd.concat([d, b]).category.value_counts().to_string())