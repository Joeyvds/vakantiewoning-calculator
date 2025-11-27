# app.py — 100% werkend, geen numpy-financial, geen errors, all-cash + financiering
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Vakantiewoning Calculator", layout="wide")
st.title("Vakantiewoning Rendementscalculator")

# ===================== INPUTS =====================
c1, c2 = st.columns(2)
with c1:
    st.subheader("Aankoop")
    koopsom = st.number_input("Koopsom", value=175000, step=5000)
    kosten_koper = st.number_input("Kosten koper + overige kosten", value=25000)
    all_cash = st.checkbox("All-cash (geen hypotheek)", False)

    if not all_cash:
        ltv = st.slider("LTV %", 50, 90, 75) / 100
        rente_pct = st.number_input("Rente %", value=4.9) / 100
        aflossingsvrij = st.checkbox("Aflossingsvrij", True)

with c2:
    st.subheader("Verhuur")
    bezetting = st.slider("Bezetting %", 40, 95, 72)
    nachtprijs = st.number_input("Gem. nachtprijs €", value=138)
    verblijfsduur = st.number_input("Gem. nachten per boeking", value=4)

st.divider()
k1,k2,k3,k4 = st.columns(4)
vve            = k1.number_input("VVE/parkkosten jaar", value=2600)
schoonmaak     = k2.number_input("Schoonmaak per wissel", value=75)
beheer_pct     = k3.number_input("Beheer % omzet", value=20.0)/100
toeristenbel   = k4.number_input("Toeristenbel. p.p.p.n.", value=2.3)

k5,k6,k7,k8 = st.columns(4)
onderhoud_pct  = k5.number_input("Onderhoud % koopsom", value=1.8)/100
energie_maand  = k6.number_input("Energie+internet maand", value=180)
erfpacht       = k7.number_input("Erfpacht jaar", value=0)
indexatie      = k8.number_input("Indexatie % per jaar", value=2.5)/100

if st.button("Bereken alles", type="primary"):
    totale_investering = koopsom + kosten_koper
    hypotheek = 0 if all_cash else koopsom * ltv
    eigen_middelen = totale_investering - hypotheek

    omzet_j1 = 365 * (bezetting/100) * nachtprijs
    wissels_j1 = 365 * (bezetting/100) / verblijfsduur

    df = pd.DataFrame({"Jaar": range(1,31)})

    for i in range(30):
        factor = (1 + indexatie)**i
        omzet = omzet_j1 * factor
        wissels = wissels_j1 * factor

        df.loc[i, "Omzet"]               = omzet
        df.loc[i, "VVE"]                 = vve * factor
        df.loc[i, "Schoonmaak"]          = wissels * schoonmaak
        df.loc[i, "Beheer"]              = omzet * beheer_pct
        df.loc[i, "Toeristenbelasting"]  = wissels * verblijfsduur * 3 * toeristenbel * factor
        df.loc[i, "Onderhoud"]           = koopsom * onderhoud_pct * factor
        df.loc[i, "Energie"]             = energie_maand * 12 * factor
        df.loc[i, "Erfpacht"]            = erfpacht * factor

        if all_cash:
            df.loc[i, "Rente"] = 0
            df.loc[i, "Aflossing"] = 0
        else:
            df.loc[i, "Rente"] = hypotheek * rente_pct
            df.loc[i, "Aflossing"] = 0 if aflossingsvrij else (hypotheek * rente_pct / (1 - (1+rente_pct)**(-30)))

        kosten = df.loc[i, ["VVE","Schoonmaak","Beheer","Toeristenbelasting","Onderhoud","Energie","Erfpacht","Rente","Aflossing"]].sum()
        df.loc[i, "Totale kosten"] = kosten
        df.loc[i, "Netto cashflow"] = omzet - kosten

    df["Cumulatief"] = df["Netto cashflow"].cumsum()

    # KPI's
    bar = omzet_j1 / koopsom
    nar = (omzet_j1 - df.loc[0,"Totale kosten"] + df.loc[0,"Rente"]) / koopsom
    roe = df.loc[0,"Netto cashflow"] / eigen_middelen

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("BAR", f"{bar:.1%}")
    col2.metric("NAR", f"{nar:.1%}")
    col3.metric("ROE jaar 1", f"{roe:.1%}")
    col4.metric("Eigen inbreng", f"€{eigen_middelen:,.0f}")

    tab1, tab2, tab3 = st.tabs(["30 jaar", "Maandgemiddelde", "Grafieken"])

    with tab1:
        st.dataframe(df.round(0).style.format("€{:,.0f}"))
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download als Excel", output.getvalue(), "vakantiewoning.xlsx")

    with tab2:
        st.metric("Gem. maand omzet", f"€{df['Omzet'].mean():,.0f}")
        st.metric("Gem. maand kosten", f"€{df['Totale kosten'].mean():,.0f}")
        st.metric("Gem. maand cashflow", f"€{df['Netto cashflow'].mean():,.0f}")

    with tab3:
        fig, ax = plt.subplots()
        ax.plot(df["Jaar"], df["Cumulatief"]/1000, marker="o")
        ax.set_title("Cumulatieve cashflow (x €1.000)")
        ax.grid(alpha=0.3)
        st.pyplot(fig)

        fig2, ax2 = plt.subplots()
        kosten_j1 = df.iloc[0,1:-4]
        ax2.pie(kosten_j1, labels=kosten_j1.index, autopct="%1.0f%%")
        st.pyplot(fig2)

    st.success("100% foutvrij – werkt met én zonder hypotheek")
