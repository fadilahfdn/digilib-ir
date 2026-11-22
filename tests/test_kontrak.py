from src.preprocessing import preprocess, preprocess_steps
from src.boolean import bangun_indeks, boolean_search
from src.vsm import bangun_vsm, vsm_skor
from src.ranking import rank

DOK = {"DOC001": ["python", "data"], "DOC002": ["jaringan", "komputer"]}


def test_preprocess_mengembalikan_daftar_token():
    hasil = preprocess("Belajar Python")
    assert isinstance(hasil, list) and all(isinstance(t, str) for t in hasil)


def test_preprocess_steps_memuat_semua_tahap():
    tahap = list(preprocess_steps("Belajar Python").keys())
    assert tahap == ["teks_asli", "case_folding", "normalisasi_istilah",
                     "sanitasi", "token", "stopword_dibuang", "stem"]


def test_boolean_search_bentuk_keluaran():
    hasil = boolean_search("python", bangun_indeks(DOK), list(DOK))
    assert set(hasil) == {"doc_ids", "peringatan", "galat"}
    assert isinstance(hasil["doc_ids"], list)


def test_vsm_dan_rank_bentuk_keluaran():
    hasil = vsm_skor(["python"], bangun_vsm(DOK))
    assert set(hasil) == {"skor", "tidak_dikenal"}
    urut = rank(hasil["skor"], 5)
    assert all(isinstance(d, str) and isinstance(s, float) for d, s in urut)