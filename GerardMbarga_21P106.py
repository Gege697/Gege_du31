# Importation des modules nécessaires
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import hashlib
import os
import random
import numpy as np

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
    cols = ["Nom", "Age", "Sexe",
            "Res_Traction", "Durete", "Module_Elasticite",
            "pH", "Corrosivite", "Composition",
            "Conductivite", "Capacite_Calorifique", "Expansion",
            "Commentaire"]
    df_init = pd.DataFrame(columns=cols)
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
# PAGE AUTHENTIFICATION
# -----------------------------
def auth_page():
    st.title("🔐 Accès sécurisé au Sondage")
    left_col, right_col = st.columns([2,3])
    with left_col:
        st.markdown('<p style="font-size:30px; font-weight:bold;">Bienvenue sur le sondage !</p>', unsafe_allow_html=True)
        st.write("Veuillez vous connecter ou vous inscrire.")
    
    with right_col:
        # Connexion
        with st.expander("Connexion", expanded=True):
            st.subheader("👤 Connexion")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.button("Se connecter"):
                users = load_users()
                hashed = hash_password(password)
                matched = next((u for u in users if u.get("email")==email and u.get("password")==hashed), None)
                if matched:
                    st.session_state["logged"] = True
                    st.session_state["user"] = matched.get("nom", email)
                    st.session_state["user_email"] = email
                    st.session_state["voted"] = check_user_voted(st.session_state["user"])
                    st.success(f"Connexion réussie — bienvenue {st.session_state['user']} !")
                else:
                    st.error("Email ou mot de passe incorrect.")

        # Inscription
        with st.expander("Inscription", expanded=False):
            st.subheader("📝 Créer un compte")
            nom = st.text_input("Nom", key="reg_nom")
            age = st.number_input("Âge", 1,120, step=1, key="reg_age")
            sexe = st.selectbox("Sexe", ["Homme","Femme","Autre"], key="reg_sexe")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input("Mot de passe", type="password", key="reg_pass")
            if st.button("S'inscrire"):
                if not nom or not email_r or not password_r:
                    st.error("Veuillez remplir tous les champs obligatoires.")
                else:
                    users = load_users()
                    if any(u.get("email")==email_r for u in users):
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

# -----------------------------
# RADAR CHART
# -----------------------------
def plot_radar(data, user_row):
    categories = list(data.columns[3:-1])
    values = user_row[categories].values.flatten().tolist()
    N = len(categories)
    
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    values += values[:1]  # fermer le cercle
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    ax.plot(angles, values, color='red', linewidth=2, label=user_row["Nom"].values[0])
    ax.fill(angles, values, color='red', alpha=0.25)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0,100)
    
    ax.set_title("Évaluation des sous-propriétés", size=15, pad=20)
    st.pyplot(fig)

# -----------------------------
# PAGE PRINCIPALE
# -----------------------------
def main():
    if not st.session_state.get("logged", False):
        auth_page()
        return
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 Déconnexion"):
        for k in ["logged","user","user_email","voted"]:
            if k in st.session_state: del st.session_state[k]
        return
    
    st.title("📊 Collecte de données sur les propriétés d'un matériau au choix")
    
    try:
        df_res = pd.read_excel(DATA_FILE)
    except:
        df_res = pd.DataFrame(columns=["Nom","Age","Sexe",
            "Res_Traction", "Durete", "Module_Elasticite",
            "pH", "Corrosivite", "Composition",
            "Conductivite", "Capacite_Calorifique", "Expansion",
            "Commentaire"])
    
    if st.session_state.get("voted", False):
        st.subheader(f"Bon retour sur ce sondage {st.session_state.get('user','')} !")
        st.warning("❌ Vous avez déjà répondu au sondage. Merci !")
    else:
        st.subheader(f"Bienvenue {st.session_state.get('user','')} !")
        with st.form("form_sondage"):
            st.markdown("### Propriétés mécaniques")
            res_traction = st.slider("Résistance à la traction", 0,100,50)
            durete = st.slider("Dureté",0,100,50)
            module_elasticite = st.slider("Module d'élasticité",0,100,50)
            
            st.markdown("### Propriétés chimiques")
            ph = st.slider("pH",0,100,50)
            corrosivite = st.slider("Corrosivité",0,100,50)
            composition = st.slider("Composition",0,100,50)
            
            st.markdown("### Propriétés thermiques")
            conductivite = st.slider("Conductivité",0,100,50)
            capacite_calorifique = st.slider("Capacité calorifique",0,100,50)
            expansion = st.slider("Expansion",0,100,50)
            
            commentaire = st.text_area("Commentaire")
            submit = st.form_submit_button("Envoyer")
        
        if submit:
            if not commentaire.strip():
                st.error("Veuillez ajouter un commentaire.")
            else:
                users = load_users()
                current_user = next((u for u in users if u.get("nom") == st.session_state["user"]), {})
                age = current_user.get("age","")
                sexe = current_user.get("sexe","")
                new_row = pd.DataFrame({
                    "Nom":[st.session_state["user"]],
                    "Age":[age],
                    "Sexe":[sexe],
                    "Res_Traction":[res_traction],
                    "Durete":[durete],
                    "Module_Elasticite":[module_elasticite],
                    "pH":[ph],
                    "Corrosivite":[corrosivite],
                    "Composition":[composition],
                    "Conductivite":[conductivite],
                    "Capacite_Calorifique":[capacite_calorifique],
                    "Expansion":[expansion],
                    "Commentaire":[commentaire]
                })
                df_res = pd.concat([df_res,new_row], ignore_index=True)
                df_res.to_excel(DATA_FILE, index=False)
                st.session_state["voted"] = True
                st.success("✅ Réponse enregistrée !")

    # Afficher le radar chart pour le dernier utilisateur
    if st.session_state.get("voted", False):
        plot_radar(df_res, df_res[df_res["Nom"]==st.session_state["user"]])

# -----------------------------
# EXECUTION
# -----------------------------
main()
