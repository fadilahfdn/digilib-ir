def bangun_vsm(dokumen_token):
    return {"doc_ids": list(dokumen_token)}


def vsm_skor(query_token, model):
    # STUB: skor tiruan agar halaman bisa dibangun
    ids = model["doc_ids"][:5]
    return {"skor": {d: round(0.9 - 0.1 * i, 4) for i, d in enumerate(ids)},
            "tidak_dikenal": []}