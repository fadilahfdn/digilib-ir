import streamlit as st

st.set_page_config(page_title="DigiLib-IR", layout="wide")

menu = st.navigation([
    st.Page("halaman/pencarian.py", title="Pencarian"),
    st.Page("halaman/inspeksi.py", title="Inspeksi Preprocessing"),
    st.Page("halaman/dataset.py", title="Dataset"),
    st.Page("halaman/evaluasi.py", title="Evaluasi"),
])
menu.run()