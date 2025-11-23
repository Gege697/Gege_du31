# Importation des modules nécessaires
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import hashlib
import os
import random


# -----------------------------
# FICHIERS
# -----------------------------
USER_FILE = "users.json"
DATA_FILE = "resultats.xlsx"

# Création des fichiers si absents
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump({"utilisateurs": []}, f, indent=4, ensure_ascii=False)

if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Nom", "Age", "Sexe", "Avis", "Commentaire"])
    df_init.to_excel(DATA_FILE, index=False)

# -----------------------------
# UTILITAIRES
# -----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("utilisateurs", [])
    except:
        return []

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump({"utilisateurs": users}, f, indent=4, ensure_ascii=False)

def check_user_voted(username: str) -> bool:
    if not os.path.exists(DATA_FILE):
        return False
    try:
        df = pd.read_excel(DATA_FILE)
        return username in df.get("Nom", []).tolist()
    except:
        return False

# -----------------------------
# SESSION : initialisation sûre
# -----------------------------
session_keys_defaults = {
    "logged": False,
    "user": "",
    "user_email": "",
    "voted": False,
    "reset_step": None,
    "reset_code": None,
    "reset_email_val": None
}

for key, default in session_keys_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -----------------------------
# PAGE AUTHENTIFICATION (expanders à droite)
# -----------------------------
def auth_page():
    st.title("🔐 Accès sécurisé au Sondage")
    left_col, right_col = st.columns([2, 3])

    # --- Colonne gauche : message ou illustration ---
    with left_col:
        st.markdown('<p style="font-size:30px; font-weight:bold;">Bienvenue sur le sondage !</p>', unsafe_allow_html=True)

        st.write("Veuillez vous connecter si vous découvrez la page\
                 ou vous inscrire à droite.")

    # --- Colonne droite : expanders Connexion / Inscription / Mot de passe oublié ---
    with right_col:
        # Connexion
        with st.expander("Connexion", expanded=True):
            st.subheader("👤 Connexion")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.button("Se connecter"):
                users = load_users()
                hashed = hash_password(password)
                matched = None
                for u in users:
                    if u.get("email") == email and u.get("password") == hashed:
                        matched = u
                        break
                if matched:
                    st.session_state["logged"] = True
                    st.session_state["user"] = matched.get("nom", email)
                    st.session_state["user_email"] = email
                    st.session_state["voted"] = check_user_voted(st.session_state.get("user",""))
                    st.success(f"Connexion réussie — bienvenue {st.session_state['user']} !")
                else:
                    st.error("Email ou mot de passe incorrect.")

        # Inscription
        with st.expander("Inscription", expanded=False):
            st.subheader("📝 Créer un compte")
            nom = st.text_input("Nom", key="reg_nom")
            age = st.number_input("Âge", min_value=1, max_value=120, step=1, key="reg_age")
            sexe = st.selectbox("Sexe", ["Homme", "Femme", "Autre"], key="reg_sexe")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input("Mot de passe", type="password", key="reg_pass")
            if st.button("S'inscrire"):
                if not nom or not email_r or not password_r:
                    st.error("Veuillez remplir tous les champs obligatoires.")
                else:
                    users = load_users()
                    if any(u.get("email") == email_r for u in users):
                        st.error("Cet email est déjà utilisé.")
                    else:
                        users.append({
                            "nom": nom,
                            "email": email_r,
                            "age": int(age),
                            "sexe": sexe,
                            "password": hash_password(password_r)
                        })
                        save_users(users)
                        st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")

        # Mot de passe oublié
        with st.expander("Mot de passe oublié", expanded=False):
            st.subheader("🔄 Réinitialisation du mot de passe")
            if st.session_state["reset_step"] is None:
                st.session_state["reset_step"] = "email"

            # Étape 1 : email
            if st.session_state["reset_step"] == "email":
                rp_email = st.text_input("Entrez votre email", key="reset_email_input")
                if st.button("Envoyer code"):
                    users = load_users()
                    if any(u.get("email") == rp_email for u in users):
                        code = str(random.randint(100000,999999))
                        st.session_state["reset_email_val"] = rp_email
                        st.session_state["reset_code"] = code
                        st.session_state["reset_step"] = "code"
                        st.info(f"📩 Code de vérification (affiché localement) : **{code}**")
                    else:
                        st.error("Aucun compte trouvé avec cet email.")

            # Étape 2 : code
            elif st.session_state["reset_step"] == "code":
                st.write(f"Code envoyé à: **{st.session_state.get('reset_email_val','(inconnu)')}**")
                code_input = st.text_input("Entrez le code reçu", key="reset_code_input")
                if st.button("Vérifier code"):
                    if code_input and code_input == st.session_state.get("reset_code"):
                        st.success("Code correct — définissez un nouveau mot de passe.")
                        st.session_state["reset_step"] = "newpass"
                    else:
                        st.error("Code incorrect.")

            # Étape 3 : nouveau mot de passe
            elif st.session_state["reset_step"] == "newpass":
                new_pass = st.text_input("Nouveau mot de passe", type="password", key="new_pass")
                confirm_pass = st.text_input("Confirmez le mot de passe", type="password", key="confirm_pass")
                if st.button("Changer mot de passe"):
                    if not new_pass:
                        st.error("Le mot de passe ne peut pas être vide.")
                    elif new_pass != confirm_pass:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        users = load_users()
                        email_to_change = st.session_state.get("reset_email_val")
                        for u in users:
                            if u.get("email") == email_to_change:
                                u["password"] = hash_password(new_pass)
                                save_users(users)
                                st.success("Mot de passe réinitialisé avec succès !")
                                st.session_state["reset_step"] = None
                                st.session_state["reset_code"] = None
                                st.session_state["reset_email_val"] = None
                                break

# -----------------------------
# PAGE PRINCIPALE (sondage)
# -----------------------------
def main():
    if not st.session_state.get("logged", False):
        auth_page()
        return

    # Déconnexion
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 Déconnexion"):
        for k in ["logged","user","user_email","voted"]:
            if k in st.session_state:
                del st.session_state[k]
        return

    # Sondage
    zone = "Ngoulemakong"
    st.title(f"📊 Sondage sur le rendu suite à l'achèvement des travaux dans la zone de {zone}")

    try:
        df_res = pd.read_excel(DATA_FILE)
    except:
        df_res = pd.DataFrame(columns=["Nom","Age","Sexe","Avis","Commentaire"])

    if st.session_state.get("voted", False):
        st.subheader(f"Heureux de vous revoir {st.session_state.get('user','')} !")
        st.warning("❌ Vous avez déjà répondu au sondage. Merci !")
    else:
        st.subheader(f"Bienvenue {st.session_state.get('user','')} !")
        with st.form("form_sondage"):
            avis = st.selectbox("Votre avis :", ["Très bon","Bon","Moyen","Mauvais"])
            commentaire = st.text_area("Commentaire")
            submit = st.form_submit_button("Envoyer")

        if submit:
            if not avis or not commentaire.strip():
                st.error("Veuillez remplir tous les champs.")
            else:
                users = load_users()
                current_user = next((u for u in users if u.get("nom") == st.session_state.get("user","")), {})
                age = current_user.get("age","")
                sexe = current_user.get("sexe","")
                new_row = pd.DataFrame({
                    "Nom":[st.session_state.get("user","")],
                    "Age":[age],
                    "Sexe":[sexe],
                    "Avis":[avis],
                    "Commentaire":[commentaire]
                })
                df_res = pd.concat([df_res,new_row], ignore_index=True)
                df_res.to_excel(DATA_FILE, index=False)
                st.session_state["voted"] = True
                st.success("✅ Réponse enregistrée ! Le formulaire n'est plus accessible.")

    # Diagramme
    st.subheader("📈 Aperçu de la tendance")
    try:
        df_plot = pd.read_excel(DATA_FILE)
    except:
        df_plot = pd.DataFrame(columns=["Nom","Age","Sexe","Avis","Commentaire"])

    if df_plot.empty or "Avis" not in df_plot.columns:
        st.info("Aucune donnée pour le moment.")
    else:
        counts = df_plot["Avis"].value_counts()
        fig, ax = plt.subplots()
        colors = ['#A3C1AD','#FFDAB9','#FFE4E1','#B0C4DE']
        ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')
        st.pyplot(fig)

# -----------------------------
# EXECUTION
# -----------------------------
main()