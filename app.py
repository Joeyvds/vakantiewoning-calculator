# app.py — kopieer alles hieronder
import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Vakantiewoning Calculator", layout="wide")
st.title("Vakantiewoning Rendementscalculator 2025")
st.markdown("### Speciaal voor recreatiewoningen, parken, erfpacht, schoonmaakkosten, etc.")

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

st.subheader("Jaarlijkse kosten (typisch voor vakantiehuizen)")
c1, c2, c3, c4 = st.columns(4)
vve = c1.number_input("VVE / parkkosten", value=2400)
schoonmaak = c2.number_input("Schoonmaakkosten per wissel", value=75)
onderhoud = c3.number_input("Onderhoud & reservering (%) van koopsom", value=2.5) / 100
energie_internet = c4.number_input("Energie + internet per maand", value=175)

c5, c6, c7, c8 = st.columns(4)
beheer = c5.number_input("Beheer / platformkosten (%) van omzet", value=18.0) / 100
toeristenbelasting = c6.number_input("Toeristenbelasting per persoon per nacht", value=2.25)
erfpacht = c7.number_input("Erfpacht per jaar (0 = geen)", value=0)
indexatie = c8.number_input("Jaarlijkse indexatie prijzen & kosten (%)", value=2.5) / 100

# --- BEREKENING ---
if st.button("Bereken rendement", type="primary"):
    hypotheek = marktwaarde * ltv
    eigen_inbreng = koopsom + (koopsom * 0.10) + 15000 - hypotheek  # 10% belastingen + bijkomend
    eigen_inbreng = max(eigen_inbreng, 1000)

    bruto_jaaromzet = (bezettingsgraad / 100) * 365 * nachtprijs
    aantal_wissels = (bezettingsgraad / 100) * 365 / verblijfsduur

    jaren = 30
    resultaten = []

    for jaar in range(1, jaren + 1):
        omzet = bruto_jaaromzet * (1 + indexatie) ** (jaar - 1)
        wissels = aantal_wissels * (1 + indexatie) ** (jaar - 1)

        kosten = (
            vve * (1 + indexatie) ** (jaar - 1) +
            wissels * schoonmaak +
            koopsom * onderhoud * (1 + indexatie) ** (jaar - 1) +
            energie_internet * 12 * (1 + indexatie) ** (jaar - 1) +
            omzet * beheer +
            (bezettingsgraad / 100 * 365 * 3) * toeristenbelasting * (1 + indexatie) ** (jaar - 1) +  # ±3 personen
            erfpacht * (1 + indexatie) ** (jaar - 1)
        )

        rente = hypotheek * rente_aflossingsvrij * 0.9  # ±90% aflossingsvrij is realistisch
        netto_cashflow = omzet - kosten - rente - extra_aflossing_per_jaar

        resultaten.append({
            "Jaar": jaar,
            "Omzet": round(omzet),
            "Kosten": round(kosten),
            "Rente": round(rente),
            "Netto cashflow": round(netto_cashflow),
            "Cumulatief cashflow": 0  # wordt hieronder berekend
        })

    df = pd.DataFrame(resultaten)
    df["Cumulatief cashflow"] = df["Netto cashflow"].cumsum()

    # Samenvatting
    bar = bruto_jaaromzet / koopsom
    nar = (bruto_jaaromzet - df["Kosten"].iloc[0]) / koopsom
    roe = df["Netto cashflow"].iloc[0] / eigen_inbreng

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BAR (Bruto AanvangsRendement)", f"{bar:.1%}")
    col2.metric("NAR (Netto AanvangsRendement)", f"{nar:.1%}")
    col3.metric("ROE (Return on Equity)", f"{roe:.1%}")
    col4.metric("Eigen inbreng", f"€{eigen_inbreng:,.0f}")

    st.subheader("30-jaars exploitatie")
    st.dataframe(df.style.format({
        "Omzet": "€{:,}", "Kosten": "€{:,}", "Rente": "€{:,}",
        "Netto cashflow": "€{:,}", "Cumulatief cashflow": "€{:,}"
    }))

    st.subheader("Cashflow ontwikkeling")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Jaar"], df["Cumulatief cashflow"] / 1000, marker="o")
    ax.set_title("Cumulatieve cashflow over 30 jaar")
    ax.set_ylabel("Duizenden euro's")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    st.success("Klaar! Deel deze link met anderen of sla op als bookmark.")
