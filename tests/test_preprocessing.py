from src.preprocessing import preprocess, preprocess_steps


def test_case_folding():
    assert preprocess("PYTHON", {"stemming": False}) == ["python"]


def test_istilah_teknis_tidak_rusak():
    token = preprocess("Belajar C++ dan C# serta TCP/IP, Wi-Fi.")
    for harus_ada in ("cplusplus", "csharp", "tcpip", "wifi"):
        assert harus_ada in token


def test_istilah_teknis_tidak_di_stem_atau_dibuang():
    assert preprocess("c++") == ["cplusplus"]


def test_stopword_indonesia_dan_inggris_dibuang():
    token = preprocess("data yang dan the of python", {"stemming": False})
    assert token == ["data", "python"]


def test_kata_penting_domain_tidak_dibuang():
    token = preprocess("operating system dan basis data", {"stemming": False})
    assert "system" in token and "basis" in token and "data" in token


def test_stemming_indonesia():
    assert preprocess("pengembangan keamanan") == ["kembang", "aman"]


def test_stemming_bisa_dimatikan():
    assert preprocess("pengembangan", {"stemming": False}) == ["pengembangan"]


def test_angka_murni_dan_satu_huruf_dibuang():
    assert preprocess("versi 3 x python3", {"stemming": False}) == ["versi", "python3"]


def test_tanda_hubung_menjadi_spasi():
    assert preprocess("front-end", {"stemming": False}) == ["front", "end"]


def test_urutan_tahap_sesuai_kontrak():
    assert list(preprocess_steps("a").keys()) == ["teks_asli", "case_folding", "normalisasi_istilah",
                                                   "sanitasi", "token", "stopword_dibuang", "stem"]