import streamlit as st
import pandas as pd
import os

# 1. POSTAVKA PROJEKTA I EXCEL BAZE
EXCEL_FILE = "GSM_Master_Lager.xlsx"

# Ako fajl ne postoji, aplikacija ga sama kreira sa tvojom strukturom
if not os.path.exists(EXCEL_FILE):
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        stakla_df = pd.DataFrame(columns=[
            "Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Tip_Stakla", 
            "Nabavna_Cena", "Prodajna_Cena", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"
        ])
        stakla_df.to_excel(writer, sheet_name="Stakla za telefone", index=False)
        
        maske_df = pd.DataFrame(columns=[
            "Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Boja", 
            "Nabavna_Cena", "Prodajna_Cena", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"
        ])
        maske_df.to_excel(writer, sheet_name="Maske", index=False)

st.title("📱 GSM MASTER - Sistem za Lager")

# 2. NAVIGACIJA KROZ SHEETOVE
meni = st.sidebar.radio("Izaberite opciju:", ["Stakla za telefone", "Maske", "PRODAJA (Kamera Skener)"])

# Učitavanje podataka iz Excela
xls = pd.ExcelFile(EXCEL_FILE)

if meni in ["Stakla za telefone", "Maske"]:
    st.header(f"📋 Pregled zaliha: {meni}")
    df = pd.read_excel(xls, sheet_name=meni)
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Magacin", int(df["Magacin"].sum()))
        col2.metric("Radnja 1", int(df["Radnja_1"].sum()))
        col3.metric("Radnja 2", int(df["Radnja_2"].sum()))
        col4.metric("Radnja 3", int(df["Radnja_3"].sum()))
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Trenutno nema unete robe u ovom listu. Dodajte artikle ispod.")
        
    with st.expander("➕ Dodaj novi artikal (Roba iz Kine)"):
        with st.form("novi_artikal"):
            barkod = st.text_input("Master Barkod:")
            naziv = st.text_input("Naziv Artikla (npr. iPhone 13):")
            sifra = st.text_input("Šifra Kase (Kolona C):")
            specifično = st.text_input("Tip (staklo) / Boja (maska):")
            p_cena = st.number_input("Prodajna cena:", min_value=0.0, step=10.0)
            n_cena = st.number_input("Nabavna cena:", min_value=0.0, step=10.0)
            
            m_kol = st.number_input("Količina Magacin:", min_value=0, step=1)
            r1_kol = st.number_input("Količina Radnja 1:", min_value=0, step=1)
            r2_kol = st.number_input("Količina Radnja 2:", min_value=0, step=1)
            r3_kol = st.number_input("Količina Radnja 3:", min_value=0, step=1)
            
            if st.form_submit_button("Sačuvaj u Excel"):
                novi_red = {
                    "Master_Barkod": str(barkod).strip(), "Naziv_Artikla": naziv, "Sifra_Kase": str(sifra).strip(),
                    "Nabavna_Cena": n_cena, "Prodajna_Cena": p_cena, "Magacin": m_kol,
                    "Radnja_1": r1_kol, "Radnja_2": r2_kol, "Radnja_3": r3_kol
                }
                if meni == "Stakla za telefone":
                    novi_red["Tip_Stakla"] = specifično
                else:
                    novi_red["Boja"] = specifično
                    
                df = pd.concat([df, pd.DataFrame([novi_red])], ignore_index=False)
                
                with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=meni, index=False)
                st.success("Artikal uspešno upisan u Excel!")
                st.rerun()

# 3. UNIVERZALNI MODUL ZA PRODAJU (KAMERA)
elif meni == "PRODAJA (Kamera Skener)":
    st.header("📸 Skeniranje kamerom telefona")
    
    izabrana_radnja = st.selectbox("Izaberite vašu radnju:", ["Radnja_1", "Radnja_2", "Radnja_3"])
    
    # OPCIJA A: Ručni unos ili eksterni skener (ako zakaže kamera)
    skenirani_kod = st.text_input("A) Ručni unos (Barkod ili Šifra kase):").strip()
    
    # OPCIJA B: Kamera direktno na ekranu za BILO KOJI TELEFON
    st.write("---")
    st.write("**B) Ili kliknite ispod da upalite kameru telefona:**")
    slika_sa_kamere = st.camera_input("Uperite kameru u barkod")
    
    # Ako je radnik slika kamerom, možemo uneti kod ručno ispod nje, 
    # ili ako koristi običan Bluetooth skener-pištolj, on odmah puni gornje polje.
    
    if st.button("PRODAJ I SKINI SA STANJA", use_container_width=True):
        if skenirani_kod:
            uspesno = False
            for sheet in ["Stakla za telefone", "Maske"]:
                trenutni_df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                
                # Pretvaramo u tekst radi lakšeg poređenja bez grešaka
                trenutni_df["Master_Barkod"] = trenutni_df["Master_Barkod"].astype(str).str.strip()
                trenutni_df["Sifra_Kase"] = trenutni_df["Sifra_Kase"].astype(str).str.strip()
                
                filter_mask = (trenutni_df["Master_Barkod"] == skenirani_kod) | (trenutni_df["Sifra_Kase"] == skenirani_kod)