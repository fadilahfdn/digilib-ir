def bangun_indeks(dokumen_token):
    # {doc_id: [token]} -> {istilah: [doc_id terurut]}
    indeks = {}
    for doc_id, tokens in dokumen_token.items():
        for t in set(tokens):
            indeks.setdefault(t, []).append(doc_id)
    return {t: sorted(ids) for t, ids in indeks.items()}


def boolean_search(query, indeks, semua_id, config=None):
    # STUB: parser belum ada, selalu mengembalikan hasil kosong
    return {"doc_ids": [], "peringatan": [], "galat": None}