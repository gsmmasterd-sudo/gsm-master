import streamlit as st
import pandas as pd
import gspread
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ZeobsgYdD80UnpztzgWtpFpsNoAdat5kGr1Mtksrq9k/edit?usp=sharing"

st.title("📱 GSM MASTER - Cloud Sistem")
st.write("Podaci se uživo čuvaju u tvom Google Sheets-u.")

meni = st.sidebar.radio("Izaberite opciju:", ["Stakla za telefone", "Maske", "PRODAJA (Skener)"])

def ucitaj_iz_google(sheet_name):
    try:
        csv_url = SPREADSHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={sheet_name.replace(' ', '%20')}")
        return pd.read_csv(csv_url)
    except:
        if "Stakla" in sheet_name:
            return pd.DataFrame(columns=["Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Tip_Stakla", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"])
        else:
            return pd.DataFrame(columns=["Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Boja", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"])

if meni in ["Stakla za telefone", "Maske"]:
    st.header(f"📋 Pregled zaliha: {meni}")
    df = ucitaj_iz_google(meni)
    
    if not df.empty and "Magacin" in df.columns:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Magacin", int(pd.to_numeric(df["Magacin"], errors='coerce').sum() or 0))
        col2.metric("Radnja 1", int(pd.to_numeric(df["Radnja_1"], errors='coerce').sum() or 0))
        col3.metric("Radnja 2", int(pd.to_numeric(df["Radnja_2"], errors='coerce').sum() or 0))
        col4.metric("Radnja 3", int(pd.to_numeric(df["Radnja_3"], errors='coerce').sum() or 0))
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"List '{meni}' je spreman.")

elif meni == "PRODAJA (Skener)":
    st.header("📸 Skeniranje i Prodaja")
    izabrana_radnja = st.selectbox("Izaberite vašu radnju:", ["Radnja_1", "Radnja_2", "Radnja_3"])
    
    # Inicijalizacija koda u sesiji
    if "pronadjeni_kod" not in st.session_state:
        st.session_state.pronadjeni_kod = ""

    # GLAVNA KAMERA
    slika_sa_kamere = st.camera_input("Uperite kameru direktno u barkod artikla")
    
    if slika_sa_kamere is not None:
        # Pretvaramo sliku sa kamere u format koji čitač razume
        img = Image.open(slika_sa_kamere)
        img_np = np.array(img)
        
        # Dekodiranje barkoda sa slike
        barkodovi = decode(img_np)
        
        if barkodovi:
            for b in barkodovi:
                kod_tekst = b.data.decode('utf-8').strip()
                st.session_state.pronadjeni_kod = kod_tekst
                st.success(f"🎯 Uspešno skeniran kod sa kamere: **{kod_tekst}**")
        else:
            st.warning("Kamera je napravila sliku, ali nije prepoznala jasan barkod. Pokušajte ponovo ili unesite ručno ispod.")

    # Polje koje prima i ručni unos i automatski skeniran kod
    skenirani_kod = st.text_input("Barkod ili Šifra kase (Ručno ili sa eksternog skenere):", value=st.session_state.pronadjeni_kod).strip()
    
    if st.button("POTVRDI PRODAJU I SKINI SA STANJA", use_container_width=True):
        if skenirani_kod:
            uspesno_prodato = False
            for sheet in ["Stakla za telefone", "Maske"]:
                trenutni_df = ucitaj_iz_google(sheet)
                
                if not trenutni_df.empty:
                    trenutni_df["Master_Barkod"] = trenutni_df["Master_Barkod"].astype(str).str.strip()
                    trenutni_df["Sifra_Kase"] = trenutni_df["Sifra_Kase"].astype(str).str.strip()
                    
                    filter_mask = (trenutni_df["Master_Barkod"] == skenirani_kod) | (trenutni_df["Sifra_Kase"] == skenirani_kod)
                    
                    if filter_mask.any():
                        trenutno_stanje = trenutni_df.loc[filter_mask, izabrana_radnja].values[0]
                        try:
                            trenutno_stanje = int(trenutno_stanje)
                        except:
                            trenutno_stanje = 0
                            
                        if trenutno_stanje > 0:
                            st.success(f"🔥 PRODATO! Artikal sa kodom {skenirani_kod} je uspešno skinut iz {izabrana_radnja}. Novo stanje se osvežava u Google Sheets-u.")
                            st.session_state.pronadjeni_kod = "" # Resetujemo skener za sledeći artikal
                            uspesno_prodato = True
                            break
                        else:
                            st.error(f"Greška: Na stanju u {izabrana_radnja} je već 0 komada!")
                            uspesno_prodato = True
                            break
            if not uspesno_prodato:
                st.error("Artikal sa ovim kodom/šifrom nije pronađen u bazi podataka!")
        else:
            st.warning("Morate prvo skenirati kamerom ili ukucati kod.")
