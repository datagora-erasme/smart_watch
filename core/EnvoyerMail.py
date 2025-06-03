import smtplib
from datetime import datetime
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
    html_content: str,
    fichier_joint: str = None,
) -> None:
    """
    Envoie un rapport par email avec contenu HTML et pièce jointe optionnelle.

    Arguments :
        emetteur (str): Adresse email de l'expéditeur
        recepteur (str): Adresse email du destinataire
        mdp_emetteur (str): Mot de passe de l'expéditeur
        smtp_server (str): Adresse du serveur SMTP
        smtp_port (int): Port du serveur SMTP
        sujet (str): Sujet de l'email
        texte (str): Texte brut de l'email
        html_content (str): Contenu HTML du corps de l'email
        fichier_joint (str, optional): Chemin du fichier HTML à joindre en pièce jointe
    """
    # Création du message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = emetteur
    msg["To"] = recepteur

    # Version texte simple
    texte = f"""
    Rapport de vérification des URLs généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}
    
    {"Consultez le fichier HTML joint pour le rapport complet avec onglets interactifs." if fichier_joint else "Consultez le contenu HTML ci-dessous pour le rapport complet."}
    """

    msg.attach(MIMEText(texte, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Joindre le fichier HTML si fourni
    if fichier_joint:
        try:
            with open(fichier_joint, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f"attachment; filename= {fichier_joint}"
                )
                msg.attach(part)
        except FileNotFoundError:
            print(
                f"Attention: Le fichier {fichier_joint} n'a pas été trouvé. Email envoyé sans pièce jointe."
            )

    # Envoi
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(emetteur, mdp_emetteur)
            server.send_message(msg)
            print("Email envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi : {e}")


# Faire un test avec les variables du .env
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    # Envoi du mail
    mail_emetteur = os.getenv("MAIL_EMETTEUR")
    mail_recepteur = os.getenv("MAIL_RECEPTEUR")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_port = int(smtp_port) if smtp_port else 587
    mdp_emetteur = os.getenv("MDP_EMETTEUR")
    sujet = "Test d'envoi d'email"
    texte = "Ceci est un test d'envoi d'email avec un contenu HTML."
    html_content = "<h1>Test Email</h1><p>Ceci est un test d'envoi d'email avec un contenu HTML.</p>"

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
