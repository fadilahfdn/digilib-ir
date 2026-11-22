TOLERANSI = 1e-9


def rank(skor, k, judul_token=None, query_token=None):
    if k is not None and k < 0:
        raise ValueError("k tidak boleh negatif")

    positif = [(doc_id, float(nilai)) for doc_id, nilai in skor.items() if nilai > 0]
    if not positif:
        return []

    positif.sort(key=lambda x: (-x[1], x[0]))
    q_unik = set(query_token or ())
    judul_map = judul_token or {}

    # Kelompokkan skor seri terhadap skor acuan klaster agar batas toleransi tetap konsisten.
    klaster = []
    grup = [positif[0]]
    acuan = positif[0][1]
    for item in positif[1:]:
        if acuan - item[1] < TOLERANSI:
            grup.append(item)
        else:
            klaster.append(grup)
            grup = [item]
            acuan = item[1]
    klaster.append(grup)

    hasil = []
    for grup in klaster:
        if len(grup) > 1:
            grup.sort(key=lambda x: (-len(q_unik & set(judul_map.get(x[0], ()))), x[0]))
        hasil.extend(grup)

    return hasil[:k] if k is not None else hasil
