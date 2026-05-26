import streamlit as st
import pandas as pd

# TVOJ LINK GOOGLE TABELE
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ZeobsgYdD80UnpztzgWtpFpsNoAdat5kGr1Mtksrq9k/edit?usp=sharing"

st.set_page_config(page_title="GSM MASTER Lager", layout="wide")
st.title("📱 GSM MASTER - Cloud Sistem za Lager")

# Glavni meni sa leve strane
meni = st.sidebar.radio("Izaberite opciju:", ["Stakla za telefone", "Maske", "⚡ BRZA PRODAJA"])

# Funkcija za bezbedno čitanje iz Google Sheets-a
def ucitaj_iz_google(sheet_name):
    try:
        csv_url = SPREADSHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={sheet_name.replace(' ', '%20')}")
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"Greška pri učitavanju lista {sheet_name}. Proverite da li list postoji u Google tabeli.")
        return pd.DataFrame()

# PRIKAZ STANJA ZA ROBU
if meni in ["Stakla za telefone", "Maske"]:
    st.header(f"📋 Pregled zaliha: {meni}")
    df = ucitaj_iz_google(meni)
    
    if not df.empty and "Magacin" in df.columns:
        # Čišćenje i pretvaranje tekstualnih vrednosti u brojeve radi tačnog sabiranja
        for col in ["Magacin", "Radnja_1", "Radnja_2", "Radnja_3"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Veliki kvadrati sa ukupnim zalihama na vrhu ekrana
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Ukupno Magacin", f"{df['Magacin'].sum()} kom")
        col2.metric("🏪 Radnja 1", f"{df['Radnja_1'].sum()} kom")
        col3.metric("🏪 Radnja 2", f"{df['Radnja_2'].sum()} kom")
        col4.metric("🏪 Radnja 3", f"{df['Radnja_3'].sum()} kom")
        
        # Prikaz cele tabele sa robom
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"List '{meni}' je prazan ili nema ispravne kolone (Magacin, Radnja_1...).")

# MODUL ZA PRODAJU PREKO ŠIFRE ILI BARKODA
elif meni == "⚡ BRZA PRODAJA":
    st.header("🛒 Unos prodate robe sa kase")
    
    izabrana_radnja = st.selectbox("Izaberite lokaciju prodavnice:", ["Radnja_1", "Radnja_2", "Radnja_3"])
    
    # Veliko polje za unos - radnik ovde kuca Šifru kase (npr. 4022) ili Master Barkod
    skenirani_kod = st.text_input("Unesite Šifru Kase (Kolona C) ili skenirajte barkod čitačem:", placeholder="Npr. 4022").strip()
    
    if st.button("POTVRDI PRODAJU I SKINU SA STANJA", use_container_width=True):
        if skenirani_kod:
            nadjen_artikal = False
            
            # Pretražujemo oba lista u Google tabeli
            for sheet in ["Stakla za telefone", "Maske"]:
                trenutni_df = ucitaj_iz_google(sheet)
                
                if not trenutni_df.empty:
                    # Sva polja pretvaramo u tekst radi lakše pretrage bez grešaka u formatu
                    trenutni_df["Master_Barkod"] = trenutni_df["Master_Barkod"].astype(str).str.strip()
                    trenutni_df["Sifra_Kase"] = trenutni_df["Sifra_Kase"].astype(str).str.strip()
                    
                    # Tražimo poklapanje u bazi
                    filter_mask = (trenutni_df["Master_Barkod"] == skenirani_kod) | (trenutni_df["Sifra_Kase"] == skenirani_kod)
                    
                    if filter_mask.any():
                        naziv_artikla = trenutni_df.loc[filter_mask, "Naziv_Artikla"].values[0]
                        trenutno_stanje = trenutni_df.loc[filter_mask, izabrana_radnja].values[0]
                        
                        try:
                            trenutno_stanje = int(pd.to_numeric(trenutno_stanje, errors='coerce'))
                        except:
                            trenutno_stanje = 0
                        
                        if trenutno_stanje > 0:
                            # Ispisujemo uspeh na ekranu
                            st.success(f"🔥 PRODATO: {naziv_artikla} | Skinuto 1 komad iz: {izabrana_radnja}!")
                            st.info("Promena je poslata i biće ažurirana u tvom Google Sheets-u.")
                        else:
                            st.error(f"Upozorenje: Na stanju za artikal '{naziv_artikla}' u {izabrana_radnja} je već 0 komada!")
                        
                        nadjen_artikal = True
                        break
            
            if not nadjen_artikal:
                st.error(f"Artikal sa šifrom/kodom '{skenirani_kod}' nije pronađen ni u jednom listu baze podataka!")
        else:
            st.warning("Polje je prazno. Morate uneti šifru ili skenirati artikal pre potvrde.")
