import math
import streamlit as st


# =========================
# CONFIGURATION PAGE
# =========================
st.set_page_config(
    page_title="Diagnostic financier d'association",
    page_icon="📊",
    layout="wide"
)


# =========================
# OUTILS
# =========================
def safe_div(numerator, denominator):
    if denominator in (0, None):
        return None
    return numerator / denominator


def euro(value):
    if value is None:
        return "N/A"
    return f"{value:,.0f} €".replace(",", " ")


def percent(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.1f} %"


def badge_ratio(value, good_min=None, warn_min=None, good_max=None, warn_max=None):
    """
    Retourne (niveau, message) avec logique simple :
    - si on raisonne en minimum : plus c'est élevé mieux c'est
    - si on raisonne en maximum : plus c'est faible mieux c'est
    """
    if value is None:
        return "gris", "Non calculable"

    # Cas "plus c'est élevé, mieux c'est"
    if good_min is not None:
        if value >= good_min:
            return "vert", "Satisfaisant"
        if warn_min is not None and value >= warn_min:
            return "orange", "Vigilance"
        return "rouge", "Alerte"

    # Cas "plus c'est faible, mieux c'est"
    if good_max is not None:
        if value <= good_max:
            return "vert", "Satisfaisant"
        if warn_max is not None and value <= warn_max:
            return "orange", "Vigilance"
        return "rouge", "Alerte"

    return "gris", "Information"


def color_box(level, title, value, comment):
    colors = {
        "vert": "#d1fae5",
        "orange": "#fed7aa",
        "rouge": "#fecaca",
        "gris": "#e5e7eb",
    }
    border = {
        "vert": "#10b981",
        "orange": "#f97316",
        "rouge": "#ef4444",
        "gris": "#9ca3af",
    }

    st.markdown(
        f"""
        <div style="
            background-color:{colors[level]};
            border-left: 6px solid {border[level]};
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 10px;">
            <div style="font-size: 0.95rem; color: #374151;">{title}</div>
            <div style="font-size: 1.35rem; font-weight: 700; margin-top: 2px;">{value}</div>
            <div style="font-size: 0.9rem; color: #374151; margin-top: 4px;">{comment}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# CALCULS
# =========================
def calcul_sig(data):
    activite_hors_subv = (
        data["ventes_prestations"]
        + data["cotisations"]
        + data["autres_produits_exploitation"]
    )
    produits_exploitation = activite_hors_subv + data["subventions_exploitation"]

    consommations_intermediaires = (
        data["achats_consommes"]
        + data["autres_charges_externes"]
    )

    valeur_ajoutee = activite_hors_subv - consommations_intermediaires

    charges_personnel = data["salaires"] + data["charges_sociales"]

    ebe = (
        valeur_ajoutee
        + data["subventions_exploitation"]
        - data["impots_taxes"]
        - charges_personnel
    )

    resultat_exploitation = (
        ebe
        - data["dotations_amortissements"]
        - data["dotations_provisions"]
    )

    resultat_financier = data["produits_financiers"] - data["charges_financieres"]
    resultat_courant = resultat_exploitation + resultat_financier

    resultat_exceptionnel = (
        data["produits_exceptionnels"] - data["charges_exceptionnelles"]
    )

    resultat_net = resultat_courant + resultat_exceptionnel

    caf = (
        resultat_net
        + data["dotations_amortissements"]
        + data["dotations_provisions"]
    )

    return {
        "activite_hors_subv": activite_hors_subv,
        "produits_exploitation": produits_exploitation,
        "consommations_intermediaires": consommations_intermediaires,
        "valeur_ajoutee": valeur_ajoutee,
        "charges_personnel": charges_personnel,
        "EBE": ebe,
        "resultat_exploitation": resultat_exploitation,
        "resultat_financier": resultat_financier,
        "resultat_courant": resultat_courant,
        "resultat_exceptionnel": resultat_exceptionnel,
        "resultat_net": resultat_net,
        "CAF": caf,
    }


def calcul_equilibres(data):
    ressources_stables = (
        data["fonds_propres"]
        + data["subventions_investissement"]
        + data["dettes_financieres_mlt"]
    )

    emplois_stables = data["immobilisations_nettes"]

    frng = ressources_stables - emplois_stables

    dettes_exploitation = (
        data["dettes_fournisseurs"]
        + data["dettes_fiscales_sociales"]
        + data["autres_dettes_exploitation"]
    )

    bfr = (
        data["stocks"]
        + data["creances_exploitation"]
        - dettes_exploitation
    )

    tresorerie_nette = frng - bfr

    actif_circulant = (
        data["stocks"]
        + data["creances_exploitation"]
        + data["disponibilites"]
    )

    total_bilan = data["immobilisations_nettes"] + actif_circulant

    dettes_ct = dettes_exploitation + data["concours_bancaires_ct"]
    dettes_financieres_totales = (
        data["dettes_financieres_mlt"] + data["concours_bancaires_ct"]
    )

    return {
        "ressources_stables": ressources_stables,
        "emplois_stables": emplois_stables,
        "FRNG": frng,
        "BFR": bfr,
        "tresorerie_nette": tresorerie_nette,
        "actif_circulant": actif_circulant,
        "total_bilan": total_bilan,
        "dettes_ct": dettes_ct,
        "dettes_financieres_totales": dettes_financieres_totales,
    }


def calcul_ratios(data, sig, eq):
    return {
        "autonomie_financiere": safe_div(data["fonds_propres"], eq["total_bilan"]),
        "endettement_financier": safe_div(
            eq["dettes_financieres_totales"], data["fonds_propres"]
        ),
        "poids_masse_salariale": safe_div(
            sig["charges_personnel"], sig["produits_exploitation"]
        ),
        "taux_subventionnement": safe_div(
            data["subventions_exploitation"], sig["produits_exploitation"]
        ),
        "marge_exploitation": safe_div(sig["EBE"], sig["produits_exploitation"]),
        "couverture_emplois_stables": safe_div(
            eq["ressources_stables"], data["immobilisations_nettes"]
        ),
        "liquidite_generale": safe_div(eq["actif_circulant"], eq["dettes_ct"]),
        "capacite_remboursement": safe_div(
            eq["dettes_financieres_totales"], sig["CAF"]
        ) if sig["CAF"] and sig["CAF"] > 0 else None,
    }


def diagnostic_global(sig, eq, ratios):
    messages = []

    # Exploitation
    if sig["EBE"] > 0:
        messages.append("✅ L'activité dégage un EBE positif : l'exploitation couvre les charges courantes avant amortissements.")
    elif sig["EBE"] == 0:
        messages.append("🟠 L'EBE est à l'équilibre : la situation d'exploitation est fragile.")
    else:
        messages.append("🔴 L'EBE est négatif : l'activité ne couvre pas les charges structurelles.")

    # Résultat net
    if sig["resultat_net"] > 0:
        messages.append("✅ Le résultat net est positif.")
    else:
        messages.append("🟠 Le résultat net est nul ou négatif : l'association doit surveiller son modèle économique.")

    # Trésorerie
    if eq["tresorerie_nette"] > 0:
        messages.append("✅ La trésorerie nette est positive.")
    else:
        messages.append("🔴 La trésorerie nette est négative : il existe une tension de financement à court terme.")

    # Dépendance subventions
    taux_subv = ratios["taux_subventionnement"]
    if taux_subv is not None:
        if taux_subv > 0.6:
            messages.append("🔴 L'association est fortement dépendante des subventions d'exploitation.")
        elif taux_subv > 0.3:
            messages.append("🟠 La dépendance aux subventions est significative.")
        else:
            messages.append("✅ La dépendance aux subventions reste modérée.")

    # Autonomie financière
    autonomie = ratios["autonomie_financiere"]
    if autonomie is not None:
        if autonomie < 0.2:
            messages.append("🔴 L'autonomie financière est faible.")
        elif autonomie < 0.35:
            messages.append("🟠 L'autonomie financière est moyenne.")
        else:
            messages.append("✅ L'autonomie financière paraît correcte.")

    # BFR
    if eq["BFR"] > 0:
        messages.append("🟠 Le BFR est positif : l'activité consomme de la trésorerie.")
    else:
        messages.append("✅ Le BFR est faible ou négatif : le cycle d'exploitation pèse peu sur la trésorerie.")

    return messages


def build_export_table(sig, eq, ratios):
    rows = [
        ("Activité hors subventions", euro(sig["activite_hors_subv"])),
        ("Produits d'exploitation", euro(sig["produits_exploitation"])),
        ("Consommations intermédiaires", euro(sig["consommations_intermediaires"])),
        ("Valeur ajoutée", euro(sig["valeur_ajoutee"])),
        ("Charges de personnel", euro(sig["charges_personnel"])),
        ("EBE", euro(sig["EBE"])),
        ("Résultat d'exploitation", euro(sig["resultat_exploitation"])),
        ("Résultat financier", euro(sig["resultat_financier"])),
        ("Résultat courant", euro(sig["resultat_courant"])),
        ("Résultat exceptionnel", euro(sig["resultat_exceptionnel"])),
        ("Résultat net", euro(sig["resultat_net"])),
        ("CAF", euro(sig["CAF"])),
        ("FRNG", euro(eq["FRNG"])),
        ("BFR", euro(eq["BFR"])),
        ("Trésorerie nette", euro(eq["tresorerie_nette"])),
        ("Autonomie financière", percent(ratios["autonomie_financiere"])),
        ("Endettement financier", f"{ratios['endettement_financier']:.2f}" if ratios["endettement_financier"] is not None else "N/A"),
        ("Poids masse salariale", percent(ratios["poids_masse_salariale"])),
        ("Taux de subventionnement", percent(ratios["taux_subventionnement"])),
        ("Marge d'exploitation", percent(ratios["marge_exploitation"])),
        ("Couverture des emplois stables", f"{ratios['couverture_emplois_stables']:.2f}" if ratios["couverture_emplois_stables"] is not None else "N/A"),
        ("Liquidité générale", f"{ratios['liquidite_generale']:.2f}" if ratios["liquidite_generale"] is not None else "N/A"),
        ("Capacité de remboursement", f"{ratios['capacite_remboursement']:.2f} ans" if ratios["capacite_remboursement"] is not None else "N/A"),
    ]
    return rows


# =========================
# INTERFACE
# =========================
st.title("📊 Diagnostic financier d'association")
st.caption("Saisissez quelques données du bilan et du compte de résultat pour obtenir une première lecture de la santé économique.")

with st.expander("ℹ️ Conseils d'utilisation", expanded=False):
    st.markdown(
        """
- Saisir les montants **en euros**.
- Ne pas mettre de séparateur de milliers.
- Si une ligne n'existe pas dans les comptes, laisser **0**.
- Le diagnostic est une **première lecture**, pas une analyse d'expert-comptable.
        """
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Compte de résultat")
    ventes_prestations = st.number_input("Ventes / prestations", min_value=0.0, value=0.0, step=1000.0)
    cotisations = st.number_input("Cotisations", min_value=0.0, value=0.0, step=1000.0)
    subventions_exploitation = st.number_input("Subventions d'exploitation", min_value=0.0, value=0.0, step=1000.0)
    autres_produits_exploitation = st.number_input("Autres produits d'exploitation", min_value=0.0, value=0.0, step=1000.0)

    achats_consommes = st.number_input("Achats consommés", min_value=0.0, value=0.0, step=1000.0)
    autres_charges_externes = st.number_input("Autres charges externes", min_value=0.0, value=0.0, step=1000.0)
    impots_taxes = st.number_input("Impôts et taxes", min_value=0.0, value=0.0, step=1000.0)
    salaires = st.number_input("Salaires", min_value=0.0, value=0.0, step=1000.0)
    charges_sociales = st.number_input("Charges sociales", min_value=0.0, value=0.0, step=1000.0)

    dotations_amortissements = st.number_input("Dotations aux amortissements", min_value=0.0, value=0.0, step=1000.0)
    dotations_provisions = st.number_input("Dotations aux provisions", min_value=0.0, value=0.0, step=1000.0)

    produits_financiers = st.number_input("Produits financiers", min_value=0.0, value=0.0, step=1000.0)
    charges_financieres = st.number_input("Charges financières", min_value=0.0, value=0.0, step=1000.0)

    produits_exceptionnels = st.number_input("Produits exceptionnels", min_value=0.0, value=0.0, step=1000.0)
    charges_exceptionnelles = st.number_input("Charges exceptionnelles", min_value=0.0, value=0.0, step=1000.0)

with col2:
    st.subheader("Bilan")
    immobilisations_nettes = st.number_input("Immobilisations nettes", min_value=0.0, value=0.0, step=1000.0)
    stocks = st.number_input("Stocks", min_value=0.0, value=0.0, step=1000.0)
    creances_exploitation = st.number_input("Créances d'exploitation", min_value=0.0, value=0.0, step=1000.0)
    disponibilites = st.number_input("Disponibilités", min_value=0.0, value=0.0, step=1000.0)

    fonds_propres = st.number_input("Fonds propres / fonds associatifs", value=0.0, step=1000.0)
    subventions_investissement = st.number_input("Subventions d'investissement", min_value=0.0, value=0.0, step=1000.0)
    dettes_financieres_mlt = st.number_input("Dettes financières moyen / long terme", min_value=0.0, value=0.0, step=1000.0)

    dettes_fournisseurs = st.number_input("Dettes fournisseurs", min_value=0.0, value=0.0, step=1000.0)
    dettes_fiscales_sociales = st.number_input("Dettes fiscales et sociales", min_value=0.0, value=0.0, step=1000.0)
    autres_dettes_exploitation = st.number_input("Autres dettes d'exploitation", min_value=0.0, value=0.0, step=1000.0)
    concours_bancaires_ct = st.number_input("Concours bancaires court terme", min_value=0.0, value=0.0, step=1000.0)

data = {
    "ventes_prestations": ventes_prestations,
    "cotisations": cotisations,
    "subventions_exploitation": subventions_exploitation,
    "autres_produits_exploitation": autres_produits_exploitation,
    "achats_consommes": achats_consommes,
    "autres_charges_externes": autres_charges_externes,
    "impots_taxes": impots_taxes,
    "salaires": salaires,
    "charges_sociales": charges_sociales,
    "dotations_amortissements": dotations_amortissements,
    "dotations_provisions": dotations_provisions,
    "produits_financiers": produits_financiers,
    "charges_financieres": charges_financieres,
    "produits_exceptionnels": produits_exceptionnels,
    "charges_exceptionnelles": charges_exceptionnelles,
    "immobilisations_nettes": immobilisations_nettes,
    "stocks": stocks,
    "creances_exploitation": creances_exploitation,
    "disponibilites": disponibilites,
    "fonds_propres": fonds_propres,
    "subventions_investissement": subventions_investissement,
    "dettes_financieres_mlt": dettes_financieres_mlt,
    "dettes_fournisseurs": dettes_fournisseurs,
    "dettes_fiscales_sociales": dettes_fiscales_sociales,
    "autres_dettes_exploitation": autres_dettes_exploitation,
    "concours_bancaires_ct": concours_bancaires_ct,
}

if st.button("Calculer le diagnostic", type="primary"):
    sig = calcul_sig(data)
    eq = calcul_equilibres(data)
    ratios = calcul_ratios(data, sig, eq)
    commentaires = diagnostic_global(sig, eq, ratios)

    st.success("Calcul réalisé.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📌 Synthèse", "📈 Soldes & équilibres", "🧮 Ratios", "📝 Commentaires"]
    )

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            niveau, commentaire = badge_ratio(sig["EBE"], good_min=0.05 * max(sig["produits_exploitation"], 1), warn_min=0)
            color_box(niveau, "EBE", euro(sig["EBE"]), commentaire)

            niveau, commentaire = badge_ratio(eq["tresorerie_nette"], good_min=0, warn_min=-1)
            color_box(niveau, "Trésorerie nette", euro(eq["tresorerie_nette"]), commentaire)

        with c2:
            niveau, commentaire = badge_ratio(ratios["autonomie_financiere"], good_min=0.35, warn_min=0.20)
            color_box(niveau, "Autonomie financière", percent(ratios["autonomie_financiere"]), commentaire)

            niveau, commentaire = badge_ratio(ratios["liquidite_generale"], good_min=1.2, warn_min=1.0)
            val = f"{ratios['liquidite_generale']:.2f}" if ratios["liquidite_generale"] is not None else "N/A"
            color_box(niveau, "Liquidité générale", val, commentaire)

        with c3:
            niveau, commentaire = badge_ratio(ratios["taux_subventionnement"], good_max=0.30, warn_max=0.60)
            color_box(niveau, "Taux de subventionnement", percent(ratios["taux_subventionnement"]), commentaire)

            niveau, commentaire = badge_ratio(ratios["capacite_remboursement"], good_max=3, warn_max=5)
            val = f"{ratios['capacite_remboursement']:.2f} ans" if ratios["capacite_remboursement"] is not None else "N/A"
            color_box(niveau, "Capacité de remboursement", val, commentaire)

    with tab2:
        st.subheader("Soldes intermédiaires et équilibres")
        col_a, col_b = st.columns(2)

        with col_a:
            st.metric("Valeur ajoutée", euro(sig["valeur_ajoutee"]))
            st.metric("EBE", euro(sig["EBE"]))
            st.metric("Résultat d'exploitation", euro(sig["resultat_exploitation"]))
            st.metric("Résultat net", euro(sig["resultat_net"]))
            st.metric("CAF", euro(sig["CAF"]))

        with col_b:
            st.metric("FRNG", euro(eq["FRNG"]))
            st.metric("BFR", euro(eq["BFR"]))
            st.metric("Trésorerie nette", euro(eq["tresorerie_nette"]))
            st.metric("Ressources stables", euro(eq["ressources_stables"]))
            st.metric("Actif circulant", euro(eq["actif_circulant"]))

    with tab3:
        st.subheader("Ratios financiers")
        ratio_data = [
            ("Autonomie financière", percent(ratios["autonomie_financiere"])),
            ("Endettement financier", f"{ratios['endettement_financier']:.2f}" if ratios["endettement_financier"] is not None else "N/A"),
            ("Poids de la masse salariale", percent(ratios["poids_masse_salariale"])),
            ("Taux de subventionnement", percent(ratios["taux_subventionnement"])),
            ("Marge d'exploitation", percent(ratios["marge_exploitation"])),
            ("Couverture des emplois stables", f"{ratios['couverture_emplois_stables']:.2f}" if ratios["couverture_emplois_stables"] is not None else "N/A"),
            ("Liquidité générale", f"{ratios['liquidite_generale']:.2f}" if ratios["liquidite_generale"] is not None else "N/A"),
            ("Capacité de remboursement", f"{ratios['capacite_remboursement']:.2f} ans" if ratios["capacite_remboursement"] is not None else "N/A"),
        ]

        for label, value in ratio_data:
            st.write(f"**{label}** : {value}")

    with tab4:
        st.subheader("Lecture automatique")
        for msg in commentaires:
            st.write(msg)

    export_rows = build_export_table(sig, eq, ratios)
    export_text = "\n".join([f"{label};{value}" for label, value in export_rows])

    st.download_button(
        label="Télécharger les résultats (CSV simple)",
        data=export_text.encode("utf-8"),
        file_name="diagnostic_association.csv",
        mime="text/csv",
    )
