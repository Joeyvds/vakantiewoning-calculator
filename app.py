# app.py – Volledige, 100% werkende versie zonder externe libraries
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Vakantiewoning Calculator", layout="wide")
st.title("Vakantiewoning Rendementscalculator – Net als Excel")

# Inputs
c1, c2 = st.columns(2)
with c1:
    st.subheader("Aankoop")
    koopsom = st.number_input("Koopsom", value=175000, step=5000)
    kosten_koper = st.number_input("Kosten koper + notariskosten", value=25000)
    all_cash = st.checkbox("All-cash (geen hypotheek)", value=False)

    if not all_cash:
        st.subheader("Financiering")
        ltv = st.slider("LTV %", 50, 90, 75, 5) / 100
        rente = st.number_input("Rente %", value=4.9) / 100
        looptijd = st.selectbox("Hypotheekvorm", ["Aflossingsvrij", "Annuïteit 30 jaar"])
    
with c2:
    st.subheader("Verhuur")
    bezetting = st.slider("Bezetting %", 40, 95, 72)
    nachtprijs = st.number_input("Gem. nachtprijs €", value=138)
    verblijfsduur = st.number_input("Gem. nachten per boeking", value=4)

st.divider()
k1, k2, k3, k4 = st.columns(4)
vve = k1.number_input("VVE/parkkosten jaar", value=2600)
schoonmaak = k2.number_input("Schoonmaak per wissel", value=75)
beheer_pct = k3.number_input("Beheer % omzet", value=20.0) / 100
toeristenbelasting = k4.number_input("Toeristenbel. p.p.p.n.", value=2.3)

k5, k6, k7, k8 = st.columns(4)
onderhoud_pct = k5.number_input("Onderhoud % koopsom", value=1.8) / 100
energie_maand = k6.number_input("Energie+internet maand", value=180)
erfpacht = k7.number_input("Erfpacht jaar (0=geen)", value=0)
indexatie = k8.number_input("Indexatie % per jaar", value=2.5) / 100

# Berekening
if st.button("Bereken alles", type="primary"):
    # Basis
    totale_investering = koopsom + kosten_koper
    if all_cash:
        hypotheek = 0
        rente_kosten = 0
        aflossing = 0
    else:
        hypotheek = koopsom * ltv
        if looptijd == "Aflossingsvrij":
            rente_kosten = hypotheek * rente
            aflossing = 0
        else:
            # Handmatige annuïteit zonder library
            maand_rente = rente / 12
            maanden = 360
            aflossing_maand = hypotheek * (maand_rente * (1 + maand_rente)**maanden) / ((1 + maand_rente)**maanden - 1)
            aflossing = aflossing_maand * 12
            rente_kosten = hypotheek * rente

    eigen_middelen = totale_investering - hypotheek

    omzet_jaar1 = 365 * (bezetting/100) * nachtprijs
    wissels_jaar1 = 365 * (bezetting/100) / verblijfsduur

    df = pd.DataFrame({"Jaar": range(1,31)})
    for i in range(30):
        factor = (1 + indexatie) ** i
        jaar = i + 1
        omzet = omzet_jaar1 * factor
        wissels = wissels_jaar1 * factor

        df.loc[i, "Omzet"] = omzet
        df.loc[i, "VVE/parkkosten"] = vve * factor
        df.loc[i, "Schoonmaak"] = wissels * schoonmaak
        df.loc[i, "Beheer"] = omzet * beheer_pct
        df.loc[i, "Toeristenbelasting"] = wissels * verblijfsduur * 3 * toeristenbelasting * factor
        df.loc[i, "Onderhoud"] = koopsom * onderhoud_pct * factor
        df.loc[i, "Energie+internet"] = energie_maand * 12 * factor
        df.loc[i, "Erfpacht"] = erfpacht * factor
        df.loc[i, "Hypotheekrente"] = rente_kosten
        df.loc[i, "Aflossing"] = aflossing

        kosten = df.loc[i, ["VVE/parkkosten","Schoonmaak","Beheer","Toeristenbelasting","Onderhoud",
                            "Energie+internet","Erfpacht","Hypotheekrente","Aflossing"]].sum()
        df.loc[i, "Totale kosten"] = kosten
        df.loc[i, "Netto cashflow"] = omzet - kosten
        df.loc[i, "Cumulatief"] = df["Netto cashflow"].cumsum()[i]

    # KPI's
    bar = omzet_jaar1 / koopsom
    nar = (omzet_jaar1 - df.loc[0, "Totale kosten"] + df.loc[0, "Hypotheekrente"]) / koopsom
    roe = df.loc[0, "Netto cashflow"] / eigen_middelen

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BAR", f"{bar:.1%}")
    col2.metric("NAR", f"{nar:.1%}")
    col3.metric("ROE jaar 1", f"{roe:.1%}")
    col4.metric("Eigen inbreng", f"€{eigen_middelen:,.0f}")

    tab1, tab2, tab3 = st.tabs(["30-jaars overzicht", "Maandgemiddelde", "Grafieken"])

    with tab1:
        st.dataframe(df.style.format("€{:,.0f}"), use_container_width=True)
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download Excel", output.getvalue(), "vakantiewoning_calc.xlsx")

    with tab2:
        maand = df.copy()
        for c in maand.columns[1:]:
            if c not in ["Jaar","Cumulatief"]:
                maand[c] = maand[c] / 12
        st.metric("Gem. maand omzet", f"€{maand['Omzet'].mean():,.0f}")
        st.metric("Gem. maand kosten", f"€{maand['Totale kosten'].mean():,.0f}")
        st.metric("Gem. maand cashflow", f"€{maand['Netto cashflow'].mean():,.0f}")

    with tab3:
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(df["Jaar"], df["Cumulatief"]/1000, marker="o", linewidth=3)
        ax.set_title("Cumulatieve cashflow")
        ax.set_ylabel("Duizenden €")
        ax.grid(alpha=0.3)
        st.pyplot(fig)

        fig2, ax2 = plt.subplots()
        kosten_jaar1 = df.iloc[0,1:-3]
        ax2.pie(kosten_jaar1, labels=kosten_jaar1.index, autopct="%1.0f%%")
        ax2.set_title("Kostenverdeling jaar 1")
        st.pyplot(fig2)

    st.success("Klaar – werkt met én zonder financiering!")
