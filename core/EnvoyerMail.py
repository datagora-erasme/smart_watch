from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def envoyer_mail_html(
    emetteur: str,
    recepteur: str,
    mdp_emetteur: str,
    smtp_server: str,
    smtp_port: int,
    sujet: str,
    texte: str,
    html_content: str = None,
    fichier_joint: str = None,
):
    """
    Envoie un email avec contenu HTML et fichier joint optionnel.

    Args:
        emetteur: Adresse email de l'expéditeur
        recepteur: Adresse email du destinataire
        mdp_emetteur: Mot de passe de l'expéditeur
        smtp_server: Serveur SMTP
        smtp_port: Port SMTP
        sujet: Sujet de l'email
        texte: Contenu texte de l'email
        html_content: Contenu HTML optionnel
        fichier_joint: Chemin vers le fichier à joindre (optionnel)
    """
    import os
    import smtplib

    try:
        # Créer le message
        msg = MIMEMultipart("alternative")
        msg["From"] = emetteur
        msg["To"] = recepteur
        msg["Subject"] = sujet

        # Ajouter le contenu texte
        msg.attach(MIMEText(texte, "plain", "utf-8"))

        # Ajouter le contenu HTML si fourni
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Ajouter le fichier joint si fourni
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

        # Détecter le type de connexion SMTP basé sur le port
        if smtp_port == 465:
            # Port 465 utilise SSL/TLS immédiat
            print(f"Connexion SMTP_SSL sur {smtp_server}:{smtp_port}")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # Autres ports utilisent SMTP standard avec starttls si nécessaire
            print(f"Connexion SMTP sur {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port)

            # Pour le port 587, utiliser starttls
            if smtp_port == 587:
                server.starttls()

        # Authentification et envoi
        server.login(emetteur, mdp_emetteur)
        server.send_message(msg)
        server.quit()

        print(f"Email envoyé avec succès de {emetteur} vers {recepteur}")

    except Exception as e:
        raise Exception(f"Erreur lors de l'envoi de l'email : {e}")


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
    mdp_emetteur = os.getenv("MDP_EMETTEUR")
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
            mdp_emetteur=mdp_emetteur,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sujet=sujet,
            texte=texte,
            html_content=html_content,
        )
        print("Email envoyé avec succès.")
    except Exception as e:
        print(f"Échec de l'envoi de l'email : {e}")
