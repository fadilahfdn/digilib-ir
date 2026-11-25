import re

import pandas as pd

BERKAS = "data/dataset.csv"

# doc_id -> pola awal teks promosi; semua teks dari pola itu sampai akhir dihapus
POTONG = {
    "DOC012": r"\s*Cetakan \d+:",
    "DOC114": r"\s*Cetakan \d+:",
    "DOC063": r"\s*Buku in akan selalu di update",
}

df = pd.read_csv(BERKAS, dtype=str, keep_default_na=False)
for doc_id, pola in POTONG.items():
    i = df.index[df["doc_id"] == doc_id][0]
    lama = df.at[i, "content"]
    cocok = re.search(pola, lama)
    assert cocok, f"Penanda tidak ditemukan di {doc_id}"
    df.at[i, "content"] = lama[:cocok.start()].rstrip()
    print(f"{doc_id}: {len(lama.split())} kata -> {len(df.at[i, 'content'].split())} kata")

df.to_csv(BERKAS, index=False, encoding="utf-8")

sisa = df["content"].str.contains(r"https?://|Rp\.|Shopee|Gramedia Digital|ISBN|WhatsApp", case=False, regex=True)
print("Dokumen yang masih berisi pola promosi:", int(sisa.sum()))