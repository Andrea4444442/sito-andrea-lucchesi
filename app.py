import os
import smtplib
import io
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from dotenv import load_dotenv

load_dotenv()  # legge il file .env

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chiave-segreta-cambiami-in-produzione")


def _smtp_send(msg: EmailMessage) -> None:
    host = os.environ.get("MAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("MAIL_PORT", "587"))
    user = os.environ["MAIL_USER"]
    password = os.environ["MAIL_PASS"]

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.send_message(msg)


def send_contact_emails(nome: str, email: str, messaggio: str) -> None:
    user = os.environ["MAIL_USER"]
    to_addr = os.environ.get("MAIL_TO", user)

    # 1) Email a te (notifica)
    msg_owner = EmailMessage()
    msg_owner["Subject"] = f"[Sito] Nuovo messaggio da {nome}"
    msg_owner["From"] = f"Website Contact <{user}>"
    msg_owner["To"] = to_addr
    msg_owner["Reply-To"] = email
    msg_owner.set_content(
        "Hai ricevuto un nuovo messaggio dal form contatti.\n\n"
        f"Nome: {nome}\n"
        f"Email: {email}\n\n"
        "Messaggio:\n"
        f"{messaggio}\n"
    )
    _smtp_send(msg_owner)

    # 2) Email al visitatore (conferma)
    msg_user = EmailMessage()
    msg_user["Subject"] = "Conferma ricezione messaggio – Andrea Lucchesi"
    msg_user["From"] = f"Andrea Lucchesi <{user}>"
    msg_user["To"] = email
    msg_user.set_content(
        f"Ciao {nome},\n\n"
        "grazie per avermi contattato. Ho ricevuto correttamente il tuo messaggio e ti risponderò appena possibile.\n\n"
        "—\n"
        "Andrea Lucchesi\n"
        "Email: a.lucchesi1999@gmail.com\n"
        "LinkedIn: https://www.linkedin.com/in/andrea-lucchesi-\n"
    )
    _smtp_send(msg_user)


@app.route("/")
def home():
    return render_template("index.html", title="Home")


@app.route("/chi-sono")
def chi_sono():
    return render_template("chi-sono.html", title="Chi sono")


@app.route("/qr-code")
def qr_code():
    """Genera un QR code che punta al sito"""
    try:
        import qrcode
        from PIL import Image
        
        # URL del sito
        site_url = os.environ.get("SITE_URL", request.url_root.rstrip('/'))
        
        # Crea il QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(site_url)
        qr.make(fit=True)
        
        # Crea l'immagine con colori del tema
        img = qr.make_image(fill_color="#5eead4", back_color="#0b1220")
        
        # Salva in memoria
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except ImportError:
        # Se le librerie non sono installate, usa un servizio esterno
        site_url = os.environ.get("SITE_URL", request.url_root.rstrip('/'))
        from urllib.parse import quote
        return redirect(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(site_url)}")


@app.route("/contatti", methods=["GET", "POST"])
def contatti():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip()
        messaggio = (request.form.get("messaggio") or "").strip()

        if not nome or not email or not messaggio:
            flash("Compila tutti i campi, per favore.", "error")
            return redirect(url_for("contatti"))

        if "@" not in email or "." not in email:
            flash("Inserisci un'email valida.", "error")
            return redirect(url_for("contatti"))

        try:
            send_contact_emails(nome, email, messaggio)
        except Exception as e:
            print("ERRORE INVIO EMAIL:", repr(e))
            flash("Errore nell'invio email. Riprova o contattami via email direttamente.", "error")
            return redirect(url_for("contatti"))

        flash(f"Grazie {nome}! Messaggio inviato. Riceverai anche una mail di conferma.", "success")
        return redirect(url_for("contatti"))

    return render_template("contatti.html", title="Contatti")


if __name__ == "__main__":
    app.run(debug=True)




