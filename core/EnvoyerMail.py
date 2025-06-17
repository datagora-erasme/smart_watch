import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def envoyer_mail_html(
    emetteur,
    recepteur,
    smtp_server,
    smtp_port,
    mdp,
    sujet,
    texte,
    html_content=None,
    fichier_joint=None,
    login_smtp=None,
):
    """
    Envoie un email HTML avec pièce jointe optionnelle.
    Gère différentes configurations SMTP (ports 587 et 465) avec authentification flexible.

    Args:
        emetteur (str): Adresse email de l'expéditeur (From)
        recepteur (str): Adresse email du destinataire
        smtp_server (str): Serveur SMTP
        smtp_port (int): Port SMTP (587 pour STARTTLS, 465 pour SSL/TLS)
        mdp (str): Mot de passe pour l'authentification
        sujet (str): Sujet de l'email
        texte (str): Corps texte brut
        html_content (str, optional): Corps HTML
        fichier_joint (str, optional): Chemin du fichier à joindre
        login_smtp (str, optional): Identifiant de connexion SMTP (si différent de l'emetteur)
    """
    # Créer le message
    msg = MIMEMultipart("alternative")
    msg["From"] = emetteur
    msg["To"] = recepteur
    msg["Subject"] = sujet

    # Ajouter le corps du message (texte brut)
    if texte:
        msg.attach(MIMEText(texte, "plain", "utf-8"))

    # Ajouter le corps HTML si fourni
    if html_content:
        msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Ajouter la pièce jointe si fournie
    if fichier_joint and os.path.exists(fichier_joint):
        with open(fichier_joint, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(fichier_joint)}",
        )
        msg.attach(part)

    # Déterminer le login à utiliser
    smtp_login = login_smtp if login_smtp else emetteur

    try:
        # Configuration selon le port
        if smtp_port == 465:
            # Port 465 : SSL/TLS direct
            print(f"Connexion SMTP SSL/TLS sur le port {smtp_port}")
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                print(f"Authentification avec login: {smtp_login}")
                server.login(smtp_login, mdp)
                server.send_message(msg)
                print("✅ Email envoyé avec succès (SSL/TLS)")

        elif smtp_port == 587:
            # Port 587 : STARTTLS
            print(f"Connexion SMTP STARTTLS sur le port {smtp_port}")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                print(f"Authentification avec login: {smtp_login}")
                server.login(smtp_login, mdp)
                server.send_message(msg)
                print("✅ Email envoyé avec succès (STARTTLS)")

        else:
            # Autres ports : tentative avec STARTTLS par défaut
            print(f"Connexion SMTP générique sur le port {smtp_port}")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                try:
                    server.starttls()
                    print("STARTTLS activé")
                except smtplib.SMTPNotSupportedError:
                    print("STARTTLS non supporté, connexion non chiffrée")

                print(f"Authentification avec login: {smtp_login}")
                server.login(smtp_login, mdp)
                server.send_message(msg)
                print("✅ Email envoyé avec succès")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification SMTP : {e}")
        print(f"Vérifiez le login ({smtp_login}) et le mot de passe")
        raise
    except smtplib.SMTPConnectError as e:
        print(f"❌ Erreur de connexion au serveur SMTP : {e}")
        print(f"Vérifiez le serveur ({smtp_server}) et le port ({smtp_port})")
        raise
    except smtplib.SMTPException as e:
        print(f"❌ Erreur SMTP : {e}")
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")
        raise


# Faire un test avec les variables du .env
if __name__ == "__main__":
    import os

    from dotenv import dotenv_values, load_dotenv

    dotenv_vars = dotenv_values()
    for key in dotenv_vars.keys():
        os.environ.pop(key, None)

    # Chargement des variables d'environnement depuis le fichier .env
    load_dotenv()
    # Envoi du mail
    mail_emetteur = os.getenv("MAIL_EMETTEUR")
    mail_recepteur = os.getenv("MAIL_RECEPTEUR")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_port = int(smtp_port) if smtp_port else 587
    mdp_mail = os.getenv("MDP_MAIL")
    login_smtp = os.getenv("LOGIN_SMTP")
    # Afficher toutes les variables pour vérification
    print("Variables d'environnement chargées :")
    env_vars = list(dotenv_values().keys())
    for var in env_vars:
        value = os.getenv(var)
        print(f"{var}: '{value}'")
    sujet = "Test d'envoi d'email"
    texte = "Ceci est un test d'envoi d'email avec un contenu HTML."
    html_content = "<h1>Test Email</h1><p>Ceci est un test d'envoi d'email avec un contenu HTML.</p>"

    try:
        envoyer_mail_html(
            emetteur=mail_emetteur,
            recepteur=mail_recepteur,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            login_smtp=login_smtp or mail_emetteur,
            mdp=mdp_mail,
            sujet=sujet,
            texte=texte,
            html_content=html_content,
        )
        print("Email envoyé avec succès.")
    except Exception as e:
        print(f"Échec de l'envoi de l'email : {e}")
