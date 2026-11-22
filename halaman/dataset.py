from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.preprocessing import preprocess_steps

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"
WAJIB_KOLOM = (
    "doc_id", "title", "category", "language",
    "source", "source_id", "retrieved_at", "content",
)
DATA_CONTOH = [
    {
        "doc_id": "DOC001_CONTOH",
        "title": "Dasar Pemrograman Python dan Struktur Data",
        "author": "Contoh Penulis",
        "year": "2024",
        "category": "Pemrograman",
        "language": "mixed",
        "source": "placeholder",
        "source_id": "CONTOH-1",
        "source_url": "",
        "retrieved_at": "2026-11-22",
        "content": (
            "Dasar Pemrograman Python dan Struktur Data. "
            "Buku ini membahas konsep dasar pemrograman menggunakan bahasa Python "
            "mulai dari tipe data, percabangan, perulangan, fungsi, hingga struktur data "
            "seperti list, dictionary, dan rekursi untuk mahasiswa informatika tingkat awal."
        ),
    },
    {
        "doc_id": "DOC002_CONTOH",
        "title": "Perancangan Basis Data Relasional dan SQL",
        "author": "Contoh Penulis",
        "year": "2024",
        "category": "Basis Data",
        "language": "id",
        "source": "placeholder",
        "source_id": "CONTOH-2",
        "source_url": "",
        "retrieved_at": "2026-11-22",
        "content": (
            "Perancangan Basis Data Relasional dan SQL. "
            "Materi disusun untuk membantu pembaca merancang skema tabel yang ternormalisasi "
            "serta menulis kueri SQL untuk pengelolaan transaksi data pada aplikasi skala menengah "
            "maupun sistem informasi akademik."
        ),
    },
]


@st.cache_data(show_spinner=False)
def _muat_dataset(path_str):
    df = pd.read_csv(path_str, dtype=str, keep_default_na=False)
    for col in WAJIB_KOLOM:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib '{col}' tidak ditemukan pada dataset.")
    if df.empty:
        raise ValueError("Berkas dataset.csv kosong.")
    for opt in ("author", "year", "source_url"):
        if opt not in df.columns:
            df[opt] = ""
    return df


def _hitung_kata_sinopsis(row):
    judul = row["title"]
    isi = row["content"]
    awalan = f"{judul}."
    sinopsis = isi[len(awalan):].strip() if isi.startswith(awalan) else isi
    return len(sinopsis.split())


st.title("Dataset")
st.caption("Ringkasan koleksi buku digital, sebaran subkategori, dan contoh transformasi teks.")

df = None
mode_contoh = False

if not DATASET_PATH.exists():
    st.info("Berkas data/dataset.csv belum tersedia di repositori.")
    if st.checkbox("Tampilkan pratinjau dengan data contoh (placeholder)", value=False):
        st.warning("Pratinjau data contoh (placeholder): statistik di bawah bukan koleksi final sistem.")
        df = pd.DataFrame(DATA_CONTOH)
        mode_contoh = True
    else:
        st.stop()
else:
    try:
        with st.spinner("Memuat koleksi buku dari data/dataset.csv..."):
            df = _muat_dataset(str(DATASET_PATH))
    except Exception as exc:
        st.error(f"Gagal memuat data/dataset.csv: {exc}")
        st.stop()

sumber_unik = ", ".join(sorted({s for s in df["source"] if s})) or "-"
tanggal_unik = ", ".join(sorted({t for t in df["retrieved_at"] if t})) or "-"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Dokumen", len(df))
m2.metric("Subkategori Terisi", df["category"].nunique())
m3.metric("Sumber Data", sumber_unik)
m4.metric("Tanggal Pengambilan", tanggal_unik)

kol_kiri, kol_kanan = st.columns([3, 2])

with kol_kiri:
    df_kat = (
        df["category"]
        .value_counts()
        .rename_axis("Subkategori")
        .reset_index(name="Jumlah")
    )
    batang = alt.Chart(df_kat).mark_bar(color="#B45309").encode(
        x=alt.X("Jumlah:Q", title="Jumlah dokumen"),
        y=alt.Y("Subkategori:N", sort="-x", title=None),
        tooltip=["Subkategori", "Jumlah"],
    )
    garis_batas = alt.Chart(pd.DataFrame({"batas": [15]})).mark_rule(
        color="#5E6A75",
        strokeDash=[4, 4],
        strokeWidth=2,
    ).encode(x="batas:Q")
    grafik = (batang + garis_batas).properties(
        title="Berapa jumlah buku pada tiap subkategori?",
        height=260,
    )
    st.altair_chart(grafik, width="stretch")
    if not mode_contoh:
        st.caption("Garis putus-putus menandai batas minimum 15 dokumen per subkategori sesuai PRD 3.3.")

with kol_kanan:
    st.subheader("Distribusi Bahasa")
    hitung_bhs = df["language"].value_counts()
    total_dok = len(df)
    baris_bhs = [
        {
            "Bahasa": bhs,
            "Jumlah": int(jml),
            "Persentase": f"{(jml / total_dok) * 100:.1f}%",
        }
        for bhs, jml in hitung_bhs.items()
    ]
    st.dataframe(pd.DataFrame(baris_bhs), hide_index=True, width="stretch")

    st.subheader("Panjang Sinopsis (Kata)")
    panjang = df.apply(_hitung_kata_sinopsis, axis=1)
    ringkas_panjang = pd.DataFrame([
        {"Statistik": "Minimum", "Nilai": int(panjang.min())},
        {"Statistik": "Median", "Nilai": round(float(panjang.median()), 1)},
        {"Statistik": "Rata-rata", "Nilai": round(float(panjang.mean()), 1)},
        {"Statistik": "Maksimum", "Nilai": int(panjang.max())},
        {"Statistik": "Dokumen < 30 kata", "Nilai": int((panjang < 30).sum())},
    ])
    st.dataframe(ringkas_panjang, hide_index=True, width="stretch")

st.subheader("Contoh Dokumen Sebelum dan Sesudah Preprocessing")
opsi_dok = df.to_dict("records")
terpilih = st.selectbox(
    "Pilih dokumen untuk diperiksa",
    opsi_dok,
    format_func=lambda r: f"{r['doc_id']}: {r['title']}",
)

with st.spinner("Menjalankan preprocessing pada dokumen terpilih..."):
    hasil_prep = preprocess_steps(terpilih["content"])

penulis = terpilih["author"] or "-"
tahun = terpilih["year"] or "-"
st.caption(
    f"ID: {terpilih['doc_id']} | Subkategori: {terpilih['category']} | "
    f"Bahasa: {terpilih['language']} | Penulis: {penulis} | Tahun: {tahun} | "
    f"Sumber: {terpilih['source']} ({terpilih['retrieved_at']})"
)

col_sebelum, col_sesudah = st.columns(2)
with col_sebelum:
    st.markdown("**Sebelum diproses**")
    st.write(terpilih["content"])

with col_sesudah:
    st.markdown("**Sesudah diproses**")
    token_akhir = hasil_prep["stem"]
    st.caption(f"Total token indeks: {len(token_akhir)}")
    st.code(" ".join(token_akhir), language=None)

with st.expander("Lihat daftar metadata seluruh dokumen"):
    kolom_tampil = [
        "doc_id", "title", "author", "year",
        "category", "language", "source", "retrieved_at",
    ]
    st.dataframe(df[kolom_tampil], hide_index=True, width="stretch")
