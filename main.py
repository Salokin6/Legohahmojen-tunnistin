import re
import customtkinter as ctk
from tkinter import filedialog
import requests
import cv2
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Azuren Custom Vision -tiedot
load_dotenv()
API_KEY = os.getenv("AZURE_PREDICTION_KEY")
API_URL = os.getenv("AZURE_PREDICTION_URL")

def paivita_kuvan_esikatselu(pil_kuva):
    """Skaalaa ja asettaa kuvan näkyviin käyttöliittymän esikatseluruutuun."""
    ctk_kuva = ctk.CTkImage(light_image=pil_kuva, dark_image=pil_kuva, size=(330, 400))
    kuva_label.configure(image=ctk_kuva, text="")
    kuva_label.image = ctk_kuva

def analysoi_kuva_datasta(kuva_data):
    """Lähettää binäärimuotoisen kuvan API:in ja päivittää käyttöliittymän Colab-logiikalla."""
    tila_label.configure(text="Analysoidaan kuvaa...", text_color="lightgreen", font=("Verdana", 32, "bold"))
    ikkuna.update()

    headers = {
        "Prediction-Key": API_KEY,
        "Content-Type": "application/octet-stream"
    }

    try:
        vastaus = requests.post(API_URL, headers=headers, data=kuva_data)
        vastaus.raise_for_status()
        tulokset = vastaus.json()

        paras_tulos = tulokset["predictions"][0]
        predicted_name = paras_tulos["tagName"]
        predicted_prob = paras_tulos["probability"]

        kynnysarvo = 0.70

        if predicted_prob < kynnysarvo:
            tila_label.configure(
                text=f"Tulos: Ei varmuutta.\n\nMalli ei ollut tarpeeksi varma.\n(Lähin arvaus oli {predicted_name.upper()} {predicted_prob:.2%} varmuudella.)",
                text_color="orange",
                font=("Verdana", 28, "bold")
            )
        else:
            tila_label.configure(
                text=f"Kuvassa on: {predicted_name.upper()}\n({predicted_prob:.2%} varmuudella)",
                text_color="#2FA572",
                font=("Verdana", 32, "bold")
            )

    except Exception as e:
        tila_label.configure(text=f"Virhe yhteydessä API:in:\n{e}", text_color="red", font=("Verdana", 24, "bold"))

def valitse_tiedosto():
    """Avaa tiedostonhallinnan, päivittää esikatselun ja lukee valitun kuvan."""
    tiedostopolku = filedialog.askopenfilename(
        title="Valitse Lego-kuva",
        filetypes=[("Kuvat", "*.jpg *.jpeg *.png")]
    )
    if tiedostopolku:
        pil_kuva = Image.open(tiedostopolku)
        paivita_kuvan_esikatselu(pil_kuva)

        with open(tiedostopolku, "rb") as kuva:
            analysoi_kuva_datasta(kuva.read())

def ota_kuva_kameralla():
    """Avaa web-kameran DirectShow-tuella ja ottaa kuvan välilyönnillä."""
    tila_label.configure(text="Avataan kameraa...", text_color="lightgreen", font=("Verdana", 32))
    ikkuna.update()

    try:
        # cv2.CAP_DSHOW estää Windowsin MSMF-kaatumiset
        kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Kokeillaan indeksiä 1, jos oletuskamera ei aukea
        if not kamera.isOpened():
            kamera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        if not kamera.isOpened():
            tila_label.configure(text="Virhe: Kameraa ei löydy tai käyttö estetty.", text_color="red", font=("Verdana", 24))
            return

        tila_label.configure(
            text="Kamera auki.\nPaina VÄLILYÖNTIÄ ottaaksesi kuvan.\nPaina ESC peruuttaaksesi.",
            text_color="lightgreen",
            font=("Verdana", 28, "bold")
        )
        ikkuna.update()

        while True:
            ret, frame = kamera.read()
            if not ret or frame is None:
                continue

            cv2.imshow("Ota kuva (VALILYONTI = Kuvaa, ESC = Peruuta)", frame)

            nappain = cv2.waitKey(1)
            if nappain == 27:  # ESC
                tila_label.configure(text="Kameran käyttö peruttu.", text_color="lightgreen", font=("Verdana", 28, "bold"))
                break
            elif nappain == 32:  # Välilyönti
                onnistui, puskuri = cv2.imencode('.jpg', frame)
                if onnistui:
                    kuva_data = puskuri.tobytes()
                    kamera.release()
                    cv2.destroyAllWindows()

                    # Päivitetään esikatselu ja lähetetään API:lle
                    pil_kuva = Image.open(io.BytesIO(kuva_data))
                    paivita_kuvan_esikatselu(pil_kuva)
                    analysoi_kuva_datasta(kuva_data)
                    return

        kamera.release()
        cv2.destroyAllWindows()

    except Exception as e:
        tila_label.configure(text=f"Kameravirhe: {e}", text_color="red", font=("Verdana", 24, "bold"))
        cv2.destroyAllWindows()

# --- Käyttöliittymän rakennus ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

ikkuna = ctk.CTk()
ikkuna.geometry("1000x850+2000+100")
ikkuna.title("Lego Tunnistin")

otsikko = ctk.CTkLabel(ikkuna, text="| Legohahmojen Tunnistaja |", 
                       font=("Verdana", 40, "bold"), 
                       text_color="lightgreen")
otsikko.pack(pady=(15, 10))

# Napit rinnakkain
nappi_kehys = ctk.CTkFrame(ikkuna, fg_color="transparent")
nappi_kehys.pack(pady=5)

tiedosto_nappi = ctk.CTkButton(nappi_kehys, 
                               text="Valitse kuva", 
                               font=("Verdana", 24, "bold"), 
                               text_color="black", height=75, width=300, 
                               command=valitse_tiedosto, corner_radius=20, border_width=6, border_color="black")

tiedosto_nappi.grid(row=0, column=0, padx=15)

kamera_nappi = ctk.CTkButton(nappi_kehys, text="Ota kuva kameralla", font=("Verdana", 24, "bold"), text_color="black", height=75, width=300, command=ota_kuva_kameralla, corner_radius=20, border_width=6, border_color="black")
kamera_nappi.grid(row=0, column=1, padx=15)

# Kuvan esikatselukortti
kuva_kehys = ctk.CTkFrame(
    ikkuna, width=330, 
    height=400, 
    corner_radius=20,
    fg_color="lightgreen", border_color="black", border_width=10)

kuva_kehys.place(relx=0.5, rely=0.435, anchor="center")

kuva_label = ctk.CTkLabel(
    kuva_kehys, 
    text="[ Ei kuvaa valittuna ]", 
    font=("Verdana", 24, "bold"), text_color="gray")

kuva_label.place(relx=0.5, rely=0.5, anchor="center")

# Tulostekstin kehys
tulos_kehys = ctk.CTkFrame(
    ikkuna, border_color="black",
    border_width=10, corner_radius=20)

tulos_kehys.pack(pady=(75, 5), padx=10, anchor="s", expand=True)

tila_label = ctk.CTkLabel(tulos_kehys,
                           text="Tervetuloa! Aloita valitsemalla kuva tai avaa kamera.", 
                           font=("Verdana", 32, "bold"), 
                           text_color="lightgreen", 
                           wraplength=900, justify="center")
tila_label.pack(pady=85, padx=60)

ikkuna.mainloop()