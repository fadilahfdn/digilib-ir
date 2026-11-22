import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RESULTS_PATH = Path(__file__).resolve().parent.parent / "evaluation" / "results.json"

CONTOH_HASIL = {
    "queries": [
        {
            "query_id": "Q01_CONTOH",
            "query_text": "python",
            "query_type": "satu_kata",
            "boolean_query": "python",
            "relevant_count": 8,
            "vsm": {"p_at_5": 0.8, "p_at_10": 0.6, "r_at_10": 0.75, "ap": 0.785},
            "boolean": {"set_size": 7, "precision": 0.7143, "recall": 0.625},
            "errors": {
                "vsm_fp_top10": ["DOC018_CONTOH"],
                "vsm_fn": ["DOC012_CONTOH"],
                "vsm_unjudged_count": 0,
                "boolean_fp": ["DOC018_CONTOH", "DOC019_CONTOH"],
                "boolean_fn": ["DOC012_CONTOH"],
                "boolean_unjudged_count": 0,
                "note": "Contoh catatan kesalahan: kata python muncul sekilas pada buku proyek.",
            },
        },
        {
            "query_id": "Q02_CONTOH",
            "query_text": "normalisasi basis data",
            "query_type": "frasa_dua_kata",
            "boolean_query": "normalisasi AND basis AND data",
            "relevant_count": 6,
            "vsm": {"p_at_5": 0.6, "p_at_10": 0.5, "r_at_10": 0.8333, "ap": 0.7222},
            "boolean": {"set_size": 4, "precision": 0.75, "recall": 0.5},
            "errors": {
                "vsm_fp_top10": ["DOC024_CONTOH"],
                "vsm_fn": ["DOC029_CONTOH"],
                "vsm_unjudged_count": 1,
                "boolean_fp": ["DOC024_CONTOH"],
                "boolean_fn": ["DOC028_CONTOH"],
                "boolean_unjudged_count": 0,
                "note": "Contoh catatan kesalahan: kueri Boolean terlalu ketat saat istilah normalisasi tidak eksplisit.",
            },
        },
        {
            "query_id": "Q03_CONTOH",
            "query_text": "keamanan jaringan komputer",
            "query_type": "topik_spesifik",
            "boolean_query": "keamanan AND jaringan",
            "relevant_count": 12,
            "vsm": {"p_at_5": 0.8, "p_at_10": 0.7, "r_at_10": 0.5833, "ap": 0.645},
            "boolean": {"set_size": 9, "precision": 0.6667, "recall": 0.5},
            "errors": {
                "vsm_fp_top10": ["DOC048_CONTOH"],
                "vsm_fn": ["DOC104_CONTOH", "DOC108_CONTOH"],
                "vsm_unjudged_count": 0,
                "boolean_fp": ["DOC048_CONTOH"],
                "boolean_fn": ["DOC104_CONTOH"],
                "boolean_unjudged_count": 0,
                "note": "Contoh catatan kesalahan: buku memakai istilah cyber security tanpa kata keamanan.",
            },
        },
    ],
    "qualitative_summary": (
        "Ringkasan contoh (placeholder): VSM mengurutkan dokumen berdasarkan bobot istilah sehingga "
        "hasil teratas lebih padat relevansinya, sedangkan Boolean mengembalikan himpunan tanpa peringkat."
    ),
    "variations": [
        {"name": "V0", "description": "Pipeline penuh (normalisasi + stopword + stemming)", "map": 0.7174, "mean_p5": 0.7333, "mean_p10": 0.6},
        {"name": "V1", "description": "Tanpa stemming", "map": 0.695, "mean_p5": 0.7, "mean_p10": 0.5667},
    ],
}


def _muat_hasil(path_obj):
    isi = path_obj.read_text(encoding="utf-8")
    data = json.loads(isi)
    if not isinstance(data, dict) or not isinstance(data.get("queries"), list) or not data["queries"]:
        raise ValueError("Struktur JSON harus berupa objek dengan daftar 'queries' tidak kosong.")
    return data


def _rata(daftar):
    return sum(daftar) / len(daftar) if daftar else 0.0


st.title("Evaluasi")
st.caption("Hasil evaluasi 10 query uji, perbandingan Boolean dan VSM, analisis kesalahan, serta variasi preprocessing.")

data = None
if not RESULTS_PATH.exists():
    st.info("Berkas evaluation/results.json belum tersedia. Hasil evaluasi final dihasilkan oleh Anggota 2 setelah Gerbang 4.")
    if st.checkbox("Tampilkan pratinjau dengan data contoh (placeholder)", value=False):
        st.warning(
            "Pratinjau data contoh (placeholder): seluruh angka di bawah hanya menguji tampilan "
            "tabel dan grafik, bukan hasil evaluasi sistem."
        )
        data = CONTOH_HASIL
    else:
        st.stop()
else:
    try:
        with st.spinner("Memuat hasil evaluasi dari evaluation/results.json..."):
            data = _muat_hasil(RESULTS_PATH)
    except Exception as exc:
        st.error(f"Gagal memuat evaluation/results.json: {exc}")
        st.stop()

queries = data["queries"]
summary = data.get("summary") or {}

nilai_map = float(summary.get("map", _rata([float((q.get("vsm") or {}).get("ap", 0.0)) for q in queries])))
mean_p5 = float(summary.get("mean_p5", _rata([float((q.get("vsm") or {}).get("p_at_5", 0.0)) for q in queries])))
mean_p10 = float(summary.get("mean_p10", _rata([float((q.get("vsm") or {}).get("p_at_10", 0.0)) for q in queries])))
mean_r10 = float(summary.get("mean_r10", _rata([float((q.get("vsm") or {}).get("r_at_10", 0.0)) for q in queries])))

tab_vsm, tab_banding, tab_galat, tab_variasi = st.tabs([
    "Metrik VSM",
    "Boolean vs VSM",
    "Analisis Kesalahan",
    "Variasi Preprocessing",
])

with tab_vsm:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MAP", f"{nilai_map:.4f}")
    c2.metric("Rata-rata P@5", f"{mean_p5:.4f}")
    c3.metric("Rata-rata P@10", f"{mean_p10:.4f}")
    c4.metric("Rata-rata R@10", f"{mean_r10:.4f}")

    baris_vsm = []
    for q in queries:
        vsm = q.get("vsm") or {}
        r_total = int(q.get("relevant_count", 0))
        maks_r10 = f"{min(1.0, 10 / r_total):.4f}" if r_total > 10 else "-"
        baris_vsm.append({
            "Query ID": q.get("query_id", "-"),
            "Query": q.get("query_text", "-"),
            "Tipe": q.get("query_type", "-"),
            "Relevan (R)": r_total,
            "P@5": round(float(vsm.get("p_at_5", 0.0)), 4),
            "P@10": round(float(vsm.get("p_at_10", 0.0)), 4),
            "R@10": round(float(vsm.get("r_at_10", 0.0)), 4),
            "Maks R@10": maks_r10,
            "AP": round(float(vsm.get("ap", 0.0)), 4),
        })
    df_vsm = pd.DataFrame(baris_vsm)
    st.dataframe(df_vsm, hide_index=True, width="stretch")

    grafik_ap = alt.Chart(df_vsm).mark_bar(color="#B45309").encode(
        x=alt.X("AP:Q", scale=alt.Scale(domain=[0, 1]), title="Average Precision (AP)"),
        y=alt.Y("Query ID:N", sort=None, title=None),
        tooltip=["Query ID", "Query", "AP"],
    ).properties(
        title="Bagaimana nilai AP pada tiap query uji?",
        height=max(180, len(df_vsm) * 28),
    )
    st.altair_chart(grafik_ap, width="stretch")

with tab_banding:
    baris_banding = []
    for q in queries:
        vsm = q.get("vsm") or {}
        bl = q.get("boolean") or {}
        baris_banding.append({
            "Query ID": q.get("query_id", "-"),
            "Query Boolean": q.get("boolean_query", "-"),
            "Ukuran Boolean": int(bl.get("set_size", 0)),
            "P Boolean": round(float(bl.get("precision", 0.0)), 4),
            "R Boolean": round(float(bl.get("recall", 0.0)), 4),
            "P@5 VSM": round(float(vsm.get("p_at_5", 0.0)), 4),
            "P@10 VSM": round(float(vsm.get("p_at_10", 0.0)), 4),
            "R@10 VSM": round(float(vsm.get("r_at_10", 0.0)), 4),
            "AP VSM": round(float(vsm.get("ap", 0.0)), 4),
        })
    st.dataframe(pd.DataFrame(baris_banding), hide_index=True, width="stretch")
    st.caption("Boolean tidak memiliki nilai P@5 karena hasil berupa himpunan dokumen tanpa skor dan peringkat.")

    ringkasan_kual = data.get("qualitative_summary") or summary.get("qualitative_summary")
    if ringkasan_kual:
        st.subheader("Ringkasan Kualitatif")
        st.write(ringkasan_kual)

with tab_galat:
    baris_galat = []
    for q in queries:
        err = q.get("errors") or {}
        baris_galat.append({
            "Query ID": q.get("query_id", "-"),
            "Query": q.get("query_text", "-"),
            "FP VSM (Top-10)": len(err.get("vsm_fp_top10") or []),
            "FN VSM": len(err.get("vsm_fn") or []),
            "Di luar pool VSM": int(err.get("vsm_unjudged_count", 0)),
            "FP Boolean": len(err.get("boolean_fp") or []),
            "FN Boolean": len(err.get("boolean_fn") or []),
            "Di luar pool Boolean": int(err.get("boolean_unjudged_count", 0)),
        })
    st.dataframe(pd.DataFrame(baris_galat), hide_index=True, width="stretch")

    terpilih = st.selectbox(
        "Lihat daftar ID dokumen kesalahan per query",
        queries,
        format_func=lambda q: f"{q.get('query_id', '-')}: {q.get('query_text', '-')}",
    )
    err_detail = terpilih.get("errors") or {}
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**Model VSM (Top-10)**")
        st.write("False Positive:", ", ".join(err_detail.get("vsm_fp_top10") or []) or "-")
        st.write("False Negative:", ", ".join(err_detail.get("vsm_fn") or []) or "-")
    with k2:
        st.markdown("**Model Boolean**")
        st.write("False Positive:", ", ".join(err_detail.get("boolean_fp") or []) or "-")
        st.write("False Negative:", ", ".join(err_detail.get("boolean_fn") or []) or "-")

    catatan = err_detail.get("note") or terpilih.get("error_note")
    if catatan:
        st.info(catatan)

with tab_variasi:
    variasi = data.get("variations") or []
    if not variasi:
        st.info("Data eksperimen variasi preprocessing (V0 sampai V3) belum tersedia pada berkas hasil.")
    else:
        baris_var = [
            {
                "Variasi": v.get("name", "-"),
                "Keterangan": v.get("description", "-"),
                "MAP": round(float(v.get("map", 0.0)), 4),
                "Rata-rata P@5": round(float(v.get("mean_p5", 0.0)), 4),
                "Rata-rata P@10": round(float(v.get("mean_p10", 0.0)), 4),
            }
            for v in variasi
        ]
        st.dataframe(pd.DataFrame(baris_var), hide_index=True, width="stretch")

st.caption(
    "Catatan: Recall@10 dan MAP dihitung berbasis pool (relative recall). "
    "Dokumen di luar pool diperlakukan tidak relevan."
)
