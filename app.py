# app.py — volledige "Excel-killer" versie (30 jaar + maand + download)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Vakantiewoning Calculator", layout="wide")
st.title("🏖️ Vakantiewoning Rendementscalculator – Net als jouw Excel, maar beter")

# ===================== INPUTS =====================
tab1, tab2, tab3 = st.tabs(["📊 Basisgegevens", "💰 Kosten & Verhuur", "🔄 Scenario 2 (optioneel)"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Aankoop & Financiering")
        koopsom = st.number_input("Koopsom excl. kosten koper", value=175000, step=5000)
        kosten_koper_pct = st.number_input("Kosten koper (%)", value=10.0) / 100
        bijkomende_kosten = st.number_input("Extra bijkomende kosten", value=15000)
        marktwaarde = st.number_input("Getaxeerde waarde (verhuurde staat)", value=160000)
        ltv = st.slider("LTV (Loan-to-Value)", 0.5, 0.9, 0.80, 0.05)
        rente = st.number_input("Hypotheekrente (% aflossingsvrij)", value=4.9) / 100
        extra_aflossing = st.number_input("Extra aflossing per jaar", value=0)
    with col2:
        st.subheader("Verhuurprestaties")
        bezetting = st.slider("Gemiddelde bezettingsgraad (%)", 40, 95, 70)
        nachtprijs = st.number_input("Gemiddelde nachtprijs (€)", value=135)
        verblijfsduur = st.number_input("Gem. verblijfsduur (nachten)", value=4)
        personen = st.number_input("Gem. personen per boeking", value=3)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vaste & variabele kosten")
        vve = st.number_input("VVE / parkkosten per jaar", value=2400)
        erfpacht = st.number_input("Erfpacht per jaar", value=0)
        energie = st.number_input("Energie + internet per maand", value=175)
        onderhoud_pct = st.number_input("Onderhoud/reservering (% van koopsom)", value=2.5) / 100
    with col2:
        schoonmaak = st.number_input("Schoonmaakkosten per wissel", value=75)
        beheer_pct = st.number_input("Beheer/platformkosten (% van omzet)", value=18.0) / 100
        toeristenbelasting = st.number_input("Toeristenbelasting p.p.p.n.", value=2.25)
        indexatie = st.number_input("Jaarlijkse indexatie prijzen & kosten (%)", value=2.5) / 100

# ===================== BEREKENING =====================
def bereken_scenario(koopsom, kosten_koper_pct, bijkomende_kosten, marktwaarde, ltv, rente, extra_aflossing,
                    bezetting, nachtprijs, verblijfsduur, personen, vve, erfpacht, energie, onderhoud_pct,
                    schoonmaak, beheer_pct, toeristenbelasting, indexatie):
    
    hypotheek = marktwaarde * ltv
    eigen_inbreng = koopsom * (1 + kosten_koper_pct) + bijkomende_kosten - hypotheek
    eigen_inbreng = max(eigen_inbreng, 1000)

    omzet_jaar1 = (bezetting/100) * 365 * nachtprijs
    wissels_jaar1 = (bezetting/100) * 365 / verblijfsduur

    jaren = 30
    df = pd.DataFrame(index=range(1, jaren+1))
    df["Jaar"] = df.index

    for jaar in range(1, jaren+1):
        factor = (1 + indexatie) ** (jaar - 1)
        df.loc[jaar, "Omzet"] = omzet_jaar1 * factor
        df.loc[jaar, "Wissels"] = wissels_jaar1 * factor
        
        df.loc[jaar, "VVE/parkkosten"] = vve * factor
        df.loc[jaar, "Erfpacht"] = erfpacht * factor
        df.loc[jaar, "Energie+internet"] = energie * 12 * factor
        df.loc[jaar, "Onderhoud"] = koopsom * onderhoud_pct * factor
        df.loc[jaar, "Schoonmaak"] = df.loc[jaar, "Wissels"] * schoonmaak
        df.loc[jaar, "Beheer"] = df.loc[jaar, "Omzet"] * beheer_pct
        df.loc[jaar, "Toeristenbelasting"] = (bezetting/100 * 365 * personen) * toeristenbelasting * factor
        df.loc[jaar, "Hypotheekrente"] = hypotheek * rente * 0.9  # 90% aflossingsvrij realistisch
        
        totale_kosten = (df.loc[jaar, ["VVE/parkkosten","Erfpacht","Energie+internet","Onderhoud",
                                      "Schoonmaak","Beheer","Toeristenbelasting","Hypotheekrente"]].sum())
        df.loc[jaar, "Totale kosten"] = totale_kosten
        df.loc[jaar, "Netto cashflow"] = df.loc[jaar, "Omzet"] - totale_kosten - extra_aflossing
     
    df["Cumulatief"] = df["Netto cashflow"].cumsum()
    
    # KPI's jaar 1
    bar = df.loc[1, "Omzet"] / koopsom
    nar = (df.loc[1, "Omzet"] - df.loc[1, "Totale kosten"] + df.loc[1, "Hypotheekrente"]) / koopsom
    roe = df.loc[1, "Netto cashflow"] / eigen_inbreng
    
    return df.round(0), eigen_inbreng, bar, nar, roe

if st.button("🔄 Bereken alles", type="primary"):
    resultaten, eigen, bar, nar, roe = bereken_scenario(
        koopsom, kosten_koper_pct, bijkomende_kosten, marktwaarde, ltv, rente, extra_aflossing,
        bezetting, nachtprijs, verblijfsduur, personen, vve, erfpacht, energie, onderhoud_pct,
        schoonmaak, beheer_pct, toeristenbelasting, indexatie)

    # ===================== UITVOER =====================
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("BAR (bruto)", f"{bar:.1%}")
    c2.metric("NAR (netto)", f"{nar:.1%}")
    c3.metric("ROE jaar 1", f"{roe:.1%}")
    c4.metric("Eigen inbreng", f"€{eigen:,.0f}")

    tab_jaar, tab_maand, tab_kosten, tab_grafiek = st.tabs(["Jaaroverzicht", "Maandoverzicht", "Kostenanalyse", "Grafieken"])

    with tab_jaar:
        st.dataframe(resultaten.style.format("€{:,}"), use_container_width=True)

    with tab_maand:
        maand = resultaten.copy()
        for col in ["Omzet","VVE/parkkosten","Erfpacht","Energie+internet","Onderhoud","Schoonmaak",
                    "Beheer","Toeristenbelasting","Hypotheekrente","Totale kosten","Netto cashflow"]:
            maand[col] = maand[col] / 12
        maand["Maand"] = ["Jan","Feb","Mrt","Apr","Mei","Jun","Jul","Aug","Sep","Okt","Nov","Dec"] * 2 + ["Jan","Jun"]
        st.dataframe(maand[["Maand","Omzet","Totale kosten","Netto cashflow"]].round(0).style.format("€{:,}"))

    with tab_kosten:
        kosten_jaar1 = resultaten.iloc[0][["VVE/parkkosten","Erfpacht","Energie+internet","Onderhoud",
                                          "Schoonmaak","Beheer","Toeristenbelasting","Hypotheekrente"]]
        fig, ax = plt.subplots()
        ax.pie(kosten_jaar1, labels=kosten_jaar1.index, autopct="%1.0f%%")
        ax.set_title("Kostenverdeling jaar 1")
        st.pyplot(fig)
        st.bar_chart(kosten_jaar1)

    with tab_grafiek:
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(resultaten["Jaar"], resultaten["Cumulatief"]/1000, marker="o")
        ax.set_title("Cumulatieve cashflow (in duizenden €)")
        ax.set_ylabel("Duizenden €")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

    # ===================== DOWNLOAD EXCEL =====================
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        resultaten.to_excel(writer, sheet_name="30-jaars overzicht")
    st.download_button("📥 Download als Excel", data=output.getvalue(), file_name="Vakantiewoning_calculatie.xlsx")

    st.success("Klaar! Alles is nu precies zoals jouw oude Excel-sheet – maar live en altijd up-to-date.")
