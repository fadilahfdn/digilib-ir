"""Mencari kandidat istilah teknis di dataset untuk resources/technical_terms.json.

Pemakaian (dari folder utama proyek):
    python tools/cari_istilah.py data/dataset.csv
"""
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

KOLOM_TEKS = ["content", "deskripsi", "description", "sinopsis"]
KOLOM_JUDUL = ["title", "judul"]

POLA = {
    "plus/pagar (c++, c#)": r"(?<![a-z0-9])[a-z0-9]{1,12}(?:\+\+|\+|#)",
    "titik atau garis miring (node.js, tcp/ip)": r"(?<![a-z0-9])[a-z][a-z0-9]*(?:[./][a-z][a-z0-9]*)+",
    "diawali titik (.net)": r"(?<![a-z0-9])\.[a-z]{2,10}(?![a-z0-9])",
    "satu huruf + tanda hubung (e-commerce)": r"(?<![a-z0-9])(?:[a-z]-[a-z]{3,}|[a-z]{3,}-[a-z])(?![a-z0-9])",
}
ABAIKAN = {"www", "com", "org", "id", "co", "html", "pdf", "dll", "dsb", "yaitu", "dst", "mis"}
URL = r"^www\.|\.(com|org|co\.id|ac\.id|go\.id|or\.id)$"


def pilih_kolom(df, kandidat):
    for k in kandidat:
        if k in df.columns:
            return k
    return None


def main(berkas):
    df = pd.read_csv(berkas)
    kolom_teks, kolom_judul = pilih_kolom(df, KOLOM_TEKS), pilih_kolom(df, KOLOM_JUDUL)
    print(f"Kolom dibaca: teks={kolom_teks}, judul={kolom_judul}, jumlah baris={len(df)}\n")
    if kolom_teks is None:
        sys.exit("Kolom teks tidak ditemukan. Kolom yang ada: " + ", ".join(df.columns))

    dokumen = (df[kolom_judul].fillna("") + ". " if kolom_judul else "") + df[kolom_teks].fillna("")
    dokumen = dokumen.str.lower()

    for nama, pola in POLA.items():
        jumlah_dok, contoh = Counter(), {}
        for teks in dokumen:
            temuan = {t.rstrip(".,;:") for t in re.findall(pola, teks)}
            temuan = {t for t in temuan if t.strip("./+#-") not in ABAIKAN and not re.fullmatch(r"[\d./]+", t) and not re.search(URL, t)}
            for t in temuan:
                jumlah_dok[t] += 1
                contoh.setdefault(t, teks[max(0, teks.find(t) - 20): teks.find(t) + len(t) + 20].replace("\n", " "))
        print(f"== {nama}: {len(jumlah_dok)} kandidat ==")
        for t, n in jumlah_dok.most_common(30):
            print(f"  {t:18} {n:3} dokumen | ...{contoh[t]}...")
        print()

    satu = Counter()
    for teks in dokumen:
        satu.update(set(re.findall(r"(?<![a-z0-9+#./-])([a-z])(?![a-z0-9+#./-])", teks)))
    print("== Token satu huruf (akan dibuang preprocessing; periksa bila ada nama bahasa seperti C atau R) ==")
    print("  " + ", ".join(f"{h}: {n} dokumen" for h, n in satu.most_common(10)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/dataset.csv")