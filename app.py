# app.py — volledige nieuwe versie met kosten-uitsplitsing + maandoverzicht
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Vakantiewoning Calculator", layout="wide")
st.title("🏖️ Vakantiewoning Rendementscalculator 2025")

# --- INPUTS ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Aankoop & Financiering")
    koopsom = st.number_input("Koopsom", value=175000)
    marktwaarde = st.number_input("Getaxeerde waarde (verhuurde staat)", value=160000)
    ltv = st.slider("LTV (Loan-to-Value)", 0.0, 1.0, 0.80, 0.05)
    rente_aflossingsvrij = st.number_input("Rente aflossingsvrij deel", value=0.049)
    extra_aflossing_per_jaar = st.number_input("Extra aflossing per jaar (optioneel)", value=0)

with col2:
    st.subheader("Verhuurprestaties")
    bezettingsgraad = st.slider("Gemiddelde bezettingsgraad (%)", 30, 95, 70)
    nachtprijs = st.number_input("Gemiddelde nachtprijs (€)", value=135)
    verblijfsduur = st.number_input("Gemiddelde verblijfsduur (nachten)", value=4)

st.subheader("Jaarlijkse kosten")
c1, c2, c3, c4 = st.columns(4)
vve = c1.number_input("VVE / parkkosten", value=2400)
schoonmaak = c2.number_input("Schoonmaakkosten per wissel", value=75)
onderhoud_pct = c3.number_input("Onderhoud & reservering (% van koopsom)", value=2.5) / 100
energie_internet = c4.number_input("Energie + internet per maand", value=175)

c5, c6, c7, c8 = st.columns(4)
beheer_pct = c5.number_input("Beheer / platformkosten (% van omzet)", value=18.0) / 100
toeristenbelasting = c6.number_input("Toeristenbelasting p.p.p.n.", value=2.25)
erfpacht = c7.number_input("Erfpacht per jaar (0 = geen)", value=0)
indexatie = c8.number_input("Jaarlijkse indexatie prijzen & kosten (%)", value=2.5) / 100

if st.button("Bereken rendement", type="primary"):
    # Basisberekeningen jaar 1
    hypotheek = marktwaarde * ltv
    eigen_inbreng = max(koopsom * 1.10 + 15000 - hypotheek, 1000)
    bruto_jaaromzet = (bezettingsgraad/100) * 365 * nachtprijs
    aantal_wissels = (bezettingsgraad/100) * 365 / verblijfsduur
    personen_per_boeking = 3

    omzet = bruto_jaaromzet
    kosten_vve = vve
    kosten_schoonmaak = aantal_wissels * schoonmaak
    kosten_onderhoud = koopsom * onderhoud_pct
    kosten_energie = energie_internet * 12
    kosten_beheer = omzet * beheer_pct
    kosten_toeristenbelasting = (bezettingsgraad/100 * 365 * personen_per_boeking) * toeristenbelasting
    kosten_erfpacht = erfpacht
    kosten_rente = hypotheek * rente_aflossingsvrij * 0.9

    totale_kosten = (kosten_vve + kosten_schoonmaak + kosten_onderhoud + kosten_energie +
                     kosten_beheer + kosten_toeristenbelasting + kosten_erfpacht + kosten_rente)
    netto_cashflow_jaar = omzet - totale_kosten - extra_aflossing_per_jaar

    # Samenvatting
    bar = omzet / koopsom
    nar = (omzet - totale_kosten + kosten_rente) / koopsom
    roe = netto_cashflow_jaar / eigen_inbreng

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BAR (Bruto)", f"{bar:.1%}")
    col2.metric("NAR (Netto)", f"{nar:.1%}")
    col3.metric("ROE", f"{roe:.1%}")
    col4.metric("Eigen inbreng", f"€{eigen_inbreng:,.0f}")

    # 1. Kostenverdeling jaar 1
    st.subheader("💰 Kostenverdeling jaar 1")
    kosten_data = {
        "Post": ["VVE/parkkosten", "Schoonmaak", "Onderhoud", "Energie+internet", "Beheer/platform", "Toeristenbelasting", "Erfpacht", "Hypotheekrente"],
        "Bedrag": [kosten_vve, kosten_schoonmaak, kosten_onderhoud, kosten_energie, kosten_beheer, kosten_toeristenbelasting, kosten_erfpacht, kosten_rente]
    }
    df_kosten = pd.DataFrame(kosten_data)
    df_kosten["Bedrag"] = df_kosten["Bedrag"].round(0).astype(int)

    col_a, col_b = st.columns(2)
    with col_a:
        fig, ax = plt.subplots(figsize=(6,6))
        ax.pie(df_kosten["Bedrag"], labels=df_kosten["Post"], autopct="%1.0f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    with col_b:
        st.dataframe(df_kosten.set_index("Post").style.format("€{:,}"))

    # 2. Gemiddelde maand
    st.subheader("📅 Gemiddelde maand")
    m1, m2, m3 = st.columns(3)
    m1.metric("Omzet per maand", f"€{omzet/12:,.0f}")
    m2.metric("Kosten per maand", f"€{totale_kosten/12:,.0f}")
    m3.metric("Cashflow per maand", f"€{(netto_cashflow_jaar)/12:,.0f}")

    st.success("Klaar! Alles is nu zichtbaar per jaar én per maand.")
