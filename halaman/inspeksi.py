from pathlib import Path

import pandas as pd
import streamlit as st

from src.preprocessing import TERLINDUNGI, preprocess_steps

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"
CONTOH_TEKS = "Pemrograman C++ dan keamanan jaringan TCP/IP menggunakan basis data MySQL."


def _isi_contoh():
    st.session_state["inspeksi_teks"] = CONTOH_TEKS


@st.cache_data(show_spinner=False)
def _muat_opsi_dokumen(path_str):
    df = pd.read_csv(path_str, dtype=str, keep_default_na=False)
    for col in ("doc_id", "title", "content"):
        if col not in df.columns:
            raise ValueError(f"Kolom wajib '{col}' tidak ditemukan pada dataset.")
    if df.empty:
        raise ValueError("Berkas dataset.csv kosong.")
    return df[["doc_id", "title", "content"]]


st.title("Inspeksi Preprocessing")
st.caption("Telusuri transformasi teks pada setiap tahap preprocessing dokumen dan query.")

sumber = st.radio(
    "Sumber teks",
    ["Ketik teks atau query", "Pilih dokumen dari dataset"],
    horizontal=True,
)

teks = ""
if sumber == "Ketik teks atau query":
    if "inspeksi_teks" not in st.session_state:
        st.session_state["inspeksi_teks"] = ""
    st.button("Muat contoh kalimat teknis", on_click=_isi_contoh)
    teks = st.text_area(
        "Masukkan teks atau query",
        key="inspeksi_teks",
        placeholder="Contoh: normalisasi basis data untuk aplikasi web",
        height=110,
    )
else:
    if not DATASET_PATH.exists():
        st.info("Berkas data/dataset.csv belum tersedia untuk dipilih.")
    else:
        try:
            with st.spinner("Memuat koleksi buku dari data/dataset.csv..."):
                df_docs = _muat_opsi_dokumen(str(DATASET_PATH))
        except Exception as exc:
            st.error(f"Gagal membaca data/dataset.csv: {exc}")
            df_docs = None

        if df_docs is not None:
            opsi = df_docs.to_dict("records")
            pilihan = st.selectbox(
                "Pilih dokumen",
                opsi,
                format_func=lambda r: f"{r['doc_id']}: {r['title']}",
            )
            teks = pilihan["content"]
            st.text_area("Teks dokumen terpilih", value=teks, height=110, disabled=True)

col1, col2, col3 = st.columns(3)
with col1:
    aktif_norm = st.checkbox("Normalisasi istilah teknis", value=True)
with col2:
    aktif_stop = st.checkbox("Stopword removal", value=True)
with col3:
    aktif_stem = st.checkbox("Stemming Sastrawi", value=True)

if not teks.strip():
    st.info("Masukkan teks di atas atau pilih dokumen koleksi untuk melihat hasil setiap tahap preprocessing.")
else:
    config = {
        "normalisasi_istilah": aktif_norm,
        "stopword": aktif_stop,
        "stemming": aktif_stem,
    }
    with st.spinner("Memproses teks melalui enam tahap preprocessing..."):
        hasil = preprocess_steps(teks, config=config)

    baris_tahap = [
        ("0. Teks asli", "Aktif", len(hasil["teks_asli"].split()), hasil["teks_asli"]),
        ("1. Case folding", "Aktif", len(hasil["case_folding"].split()), hasil["case_folding"]),
        (
            "2. Normalisasi istilah teknis",
            "Aktif" if aktif_norm else "Dimatikan",
            len(hasil["normalisasi_istilah"].split()),
            hasil["normalisasi_istilah"],
        ),
        ("3. Sanitasi karakter", "Aktif", len(hasil["sanitasi"].split()), hasil["sanitasi"]),
        (
            "4. Tokenisasi (filter angka dan 1 huruf)",
            "Aktif",
            len(hasil["token"]),
            ", ".join(hasil["token"]),
        ),
        (
            "5. Stopword removal",
            "Aktif" if aktif_stop else "Dimatikan",
            len(hasil["stopword_dibuang"]),
            ", ".join(hasil["stopword_dibuang"]),
        ),
        (
            "6. Stemming Sastrawi",
            "Aktif" if aktif_stem else "Dimatikan",
            len(hasil["stem"]),
            ", ".join(hasil["stem"]),
        ),
    ]
    df_tahap = pd.DataFrame(baris_tahap, columns=["Tahap", "Status", "Jumlah token", "Hasil"])
    st.dataframe(df_tahap, hide_index=True, width="stretch")

    token_akhir = hasil["stem"]
    if not token_akhir:
        st.warning("Semua token terhapus setelah preprocessing. Pada pencarian VSM, query ini menghasilkan vektor nol.")
    else:
        st.subheader("Ringkasan Token Akhir")
        st.caption(f"Total token hasil akhir: {len(token_akhir)}")
        st.code(" ".join(token_akhir), language=None)
        terlindungi_muncul = sorted({t for t in token_akhir if t in TERLINDUNGI})
        if terlindungi_muncul:
            st.write("Istilah teknis terlindungi yang dipertahankan:", ", ".join(terlindungi_muncul))
        else:
            st.caption("Tidak ada istilah teknis terlindungi pada token akhir.")
