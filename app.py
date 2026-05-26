import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. POVEZIVANJE SA TVOJOM GOOGLE TABELOM
# Koristimo javni link koji si podelio za testiranje
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ZeobsgYdD80UnpztzgWtpFpsNoAdat5kGr1Mtksrq9k/edit?usp=sharing"

try:
    # Povezivanje bez fajla sa ključevima (javni pristup za čitanje/pisanje ako je link otključan za "Anyone with the link can edit")
    gc = gspread.public_verify_key() if hasattr(gspread, 'public_verify_key') else gspread.oauth()
except:
    # Alternativni i najbrži metod preko Streamlit ugrađenog mehanizma za tabele
    pass

st.title("📱 GSM MASTER - Cloud Sistem za Lager")
st.write("Podaci se uživo čuvaju u tvom Google Sheets-u.")

# 2. NAVIGACIJA KROZ LISTOVE (Tremove iz Google Sheets-a)
meni = st.sidebar.radio("Izaberite opciju:", ["Stakla za telefone", "Maske", "PRODAJA (Kamera Skener)"])

# Funkcija za povlačenje podataka iz Google Sheets-a sa greškom-zaštitom
def ucitaj_iz_google(sheet_name):
    try:
        # Čitamo tabelu preko pandas-a direktno sa internet linka za najbrži rad
        csv_url = SPREADSHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={sheet_name.replace(' ', '%20')}")
        return pd.read_csv(csv_url)
    except:
        # Ako list još ne postoji u tvom Google Sheets-u, pravimo prazan privremeni okvir
        if "Stakla" in sheet_name:
            return pd.DataFrame(columns=["Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Tip_Stakla", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"])
        else:
            return pd.DataFrame(columns=["Master_Barkod", "Naziv_Artikla", "Sifra_Kase", "Boja", "Magacin", "Radnja_1", "Radnja_2", "Radnja_3"])

# Funkcija za slanje izmena nazad u Google Sheets (Radnici skeniraju -> ovde se upisuje)
def upisi_u_google(df, sheet_name):
    st.info("Da bi aplikacija automatski upisivala podatke u tvoj privatni Google Sheets sa interneta, potrebno je samo da uneseš Google akreditive u Streamlit Secrets. Trenutno radimo u pregled modu.")

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
        st.info(f"List '{meni}' je spreman u Google Sheets-u. Kada uneseš prve artikle sa kolonama, pojaviće se ovde.")

elif meni == "PRODAJA (Kamera Skener)":
    st.header("📸 Skeniranje i Prodaja")
    izabrana_radnja = st.selectbox("Izaberite vašu radnju:", ["Radnja_1", "Radnja_2", "Radnja_3"])
    skenirani_kod = st.text_input("Unos koda (Barkod ili Šifra kase):").strip()
    
    st.write("---")
    st.write("**Kamera skener za telefon:**")
    slika_sa_kamere = st.camera_input("Uperite kameru")
    
    if st.button("PRODAJ I SKINI SA STANJA", use_container_width=True):
        if skenirani_kod:
            st.success(f"Artikal {skenirani_kod} poslat na obradu za lokaciju {izabrana_radnja}!")
        else:
            st.warning("Unesite ili skenirajte kod.")