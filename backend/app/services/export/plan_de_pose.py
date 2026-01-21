"""
Génération du plan de pose pour plancher poutrelles-hourdis.

Le plan de pose est un document technique montrant:
- La disposition des poutrelles
- L'espacement (entraxe)
- Les dimensions
- Les informations techniques
"""
from io import BytesIO
from typing import Dict, Any, Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle


def generate_plan_de_pose(
    projet_info: Dict[str, Any],
    calcul_info: Dict[str, Any],
    resultats: Dict[str, Any],
    largeur_plancher: float = 10.0,  # mètres
    longueur_plancher: Optional[float] = None,  # mètres (si None, = portée)
) -> BytesIO:
    """
    Génère un plan de pose PDF pour un plancher poutrelles-hourdis.

    Args:
        projet_info: Informations du projet (nom, référence, client)
        calcul_info: Informations du calcul (nom, date)
        resultats: Résultats du calcul (poutrelle, entraxe, etc.)
        largeur_plancher: Largeur du plancher en mètres
        longueur_plancher: Longueur du plancher (portée) en mètres

    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()

    # Page en format paysage A4
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Extraire les données
    poutrelle = resultats.get('poutrelle', {})
    verification = resultats.get('verification', {})

    reference_poutrelle = poutrelle.get('reference', 'N/A')
    hauteur_hourdis = poutrelle.get('hauteur_hourdis_cm', 20)
    entraxe_cm = poutrelle.get('entraxe_cm', 60)
    epaisseur_table = poutrelle.get('epaisseur_table_cm', 5)
    hauteur_totale = poutrelle.get('hauteur_totale_cm', hauteur_hourdis + epaisseur_table)

    portee = verification.get('portee_demandee_m', 5.5)
    charge = verification.get('charge_utilisee_kg_m2', 500)

    if longueur_plancher is None:
        longueur_plancher = portee

    # Marges
    margin = 2 * cm
    draw_area_width = page_width - 2 * margin
    draw_area_height = page_height - 2 * margin - 4 * cm  # Espace pour cartouche

    # ==================== EN-TÊTE ====================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, page_height - margin, "PLAN DE POSE - PLANCHER POUTRELLES-HOURDIS")

    c.setFont("Helvetica", 10)
    c.drawString(margin, page_height - margin - 20, f"Projet: {projet_info.get('name', 'N/A')}")
    c.drawString(margin, page_height - margin - 35, f"Référence: {projet_info.get('reference', 'N/A')}")
    c.drawString(margin + 300, page_height - margin - 20, f"Calcul: {calcul_info.get('name', 'N/A')}")
    c.drawString(margin + 300, page_height - margin - 35, f"Date: {datetime.now().strftime('%d/%m/%Y')}")

    # ==================== ZONE DE DESSIN ====================
    draw_origin_x = margin
    draw_origin_y = margin + 3 * cm

    # Échelle pour le dessin (adapter à la zone disponible)
    scale_x = (draw_area_width - 100) / largeur_plancher  # pixels par mètre
    scale_y = (draw_area_height - 100) / longueur_plancher
    scale = min(scale_x, scale_y, 50)  # Max 50 pixels/m pour lisibilité

    # Origine du dessin du plancher
    plancher_x = draw_origin_x + 50
    plancher_y = draw_origin_y + 50

    plancher_width = largeur_plancher * scale
    plancher_height = longueur_plancher * scale

    # Dessiner le contour du plancher
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(plancher_x, plancher_y, plancher_width, plancher_height)

    # Calculer le nombre de poutrelles
    entraxe_m = entraxe_cm / 100.0
    nb_poutrelles = int(largeur_plancher / entraxe_m) + 1

    # Dessiner les poutrelles
    c.setStrokeColor(colors.HexColor('#1E40AF'))  # Bleu foncé
    c.setFillColor(colors.HexColor('#DBEAFE'))    # Bleu clair
    c.setLineWidth(1)

    largeur_poutrelle_px = 8  # Largeur visuelle de la poutrelle

    for i in range(nb_poutrelles):
        x = plancher_x + i * entraxe_m * scale
        if x <= plancher_x + plancher_width:
            # Rectangle pour la poutrelle
            c.rect(x - largeur_poutrelle_px/2, plancher_y, largeur_poutrelle_px, plancher_height, fill=1)

    # Dessiner les hourdis (zones entre les poutrelles)
    c.setFillColor(colors.HexColor('#FEF3C7'))  # Jaune clair
    c.setStrokeColor(colors.HexColor('#D97706'))  # Orange
    c.setLineWidth(0.5)

    for i in range(nb_poutrelles - 1):
        x1 = plancher_x + i * entraxe_m * scale + largeur_poutrelle_px/2
        x2 = plancher_x + (i + 1) * entraxe_m * scale - largeur_poutrelle_px/2
        if x2 <= plancher_x + plancher_width:
            c.rect(x1, plancher_y, x2 - x1, plancher_height, fill=1)

    # ==================== COTATIONS ====================
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)
    c.setLineWidth(0.5)
    c.setFont("Helvetica", 8)

    # Cotation de la portée (verticale, à gauche)
    cote_x = plancher_x - 30
    c.line(cote_x, plancher_y, cote_x, plancher_y + plancher_height)
    c.line(cote_x - 5, plancher_y, cote_x + 5, plancher_y)
    c.line(cote_x - 5, plancher_y + plancher_height, cote_x + 5, plancher_y + plancher_height)

    c.saveState()
    c.translate(cote_x - 15, plancher_y + plancher_height/2)
    c.rotate(90)
    c.drawCentredString(0, 0, f"Portée: {portee:.2f} m")
    c.restoreState()

    # Cotation de la largeur (horizontale, en bas)
    cote_y = plancher_y - 20
    c.line(plancher_x, cote_y, plancher_x + plancher_width, cote_y)
    c.line(plancher_x, cote_y - 5, plancher_x, cote_y + 5)
    c.line(plancher_x + plancher_width, cote_y - 5, plancher_x + plancher_width, cote_y + 5)
    c.drawCentredString(plancher_x + plancher_width/2, cote_y - 12, f"Largeur: {largeur_plancher:.2f} m")

    # Cotation de l'entraxe
    if nb_poutrelles >= 2:
        entraxe_cote_y = plancher_y + plancher_height + 15
        x1 = plancher_x
        x2 = plancher_x + entraxe_m * scale
        c.line(x1, entraxe_cote_y, x2, entraxe_cote_y)
        c.line(x1, entraxe_cote_y - 5, x1, entraxe_cote_y + 5)
        c.line(x2, entraxe_cote_y - 5, x2, entraxe_cote_y + 5)
        c.drawCentredString((x1 + x2)/2, entraxe_cote_y + 8, f"Entraxe: {entraxe_cm} cm")

    # ==================== LÉGENDE ====================
    legend_x = plancher_x + plancher_width + 40
    legend_y = plancher_y + plancher_height - 20

    c.setFont("Helvetica-Bold", 10)
    c.drawString(legend_x, legend_y, "LÉGENDE")

    c.setFont("Helvetica", 9)
    legend_y -= 25

    # Poutrelle
    c.setFillColor(colors.HexColor('#DBEAFE'))
    c.setStrokeColor(colors.HexColor('#1E40AF'))
    c.rect(legend_x, legend_y - 5, 20, 10, fill=1)
    c.setFillColor(colors.black)
    c.drawString(legend_x + 30, legend_y, f"Poutrelle {reference_poutrelle}")

    # Hourdis
    legend_y -= 20
    c.setFillColor(colors.HexColor('#FEF3C7'))
    c.setStrokeColor(colors.HexColor('#D97706'))
    c.rect(legend_x, legend_y - 5, 20, 10, fill=1)
    c.setFillColor(colors.black)
    c.drawString(legend_x + 30, legend_y, f"Hourdis {hauteur_hourdis} cm")

    # ==================== TABLEAU TECHNIQUE ====================
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(legend_x, legend_y - 40, "CARACTÉRISTIQUES")

    c.setFont("Helvetica", 9)
    specs = [
        ("Poutrelle:", reference_poutrelle),
        ("Hauteur hourdis:", f"{hauteur_hourdis} cm"),
        ("Entraxe:", f"{entraxe_cm} cm"),
        ("Épaisseur table:", f"{epaisseur_table} cm"),
        ("Hauteur totale:", f"{hauteur_totale} cm"),
        ("Portée:", f"{portee:.2f} m"),
        ("Charge:", f"{charge} kg/m²"),
        ("Nb poutrelles:", f"{nb_poutrelles}"),
    ]

    spec_y = legend_y - 55
    for label, value in specs:
        c.drawString(legend_x, spec_y, label)
        c.drawString(legend_x + 80, spec_y, str(value))
        spec_y -= 15

    # ==================== CARTOUCHE ====================
    cartouche_height = 2.5 * cm
    cartouche_y = margin

    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(margin, cartouche_y, draw_area_width, cartouche_height)

    # Divisions du cartouche
    c.line(margin + draw_area_width * 0.4, cartouche_y, margin + draw_area_width * 0.4, cartouche_y + cartouche_height)
    c.line(margin + draw_area_width * 0.7, cartouche_y, margin + draw_area_width * 0.7, cartouche_y + cartouche_height)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 10, cartouche_y + cartouche_height - 15, "ConcreteFlow")
    c.setFont("Helvetica", 8)
    c.drawString(margin + 10, cartouche_y + cartouche_height - 28, "Logiciel de calcul béton armé")
    c.drawString(margin + 10, cartouche_y + 8, f"Client: {projet_info.get('client_name', 'N/A')}")

    c.setFont("Helvetica", 9)
    c.drawString(margin + draw_area_width * 0.4 + 10, cartouche_y + cartouche_height - 15, f"Projet: {projet_info.get('name', '')}")
    c.drawString(margin + draw_area_width * 0.4 + 10, cartouche_y + cartouche_height - 28, f"Réf: {projet_info.get('reference', '')}")
    c.drawString(margin + draw_area_width * 0.4 + 10, cartouche_y + 8, f"Zone: {calcul_info.get('name', '')}")

    c.drawString(margin + draw_area_width * 0.7 + 10, cartouche_y + cartouche_height - 15, f"Échelle: 1/{int(100/scale)} environ")
    c.drawString(margin + draw_area_width * 0.7 + 10, cartouche_y + cartouche_height - 28, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawString(margin + draw_area_width * 0.7 + 10, cartouche_y + 8, "Plan de pose")

    # ==================== NOTES ====================
    notes_y = cartouche_y + cartouche_height + 10
    c.setFont("Helvetica", 7)
    c.drawString(margin, notes_y, "Notes: Ce plan est indicatif. Les dimensions doivent être vérifiées sur site. Respecter les règles de mise en œuvre du fabricant.")

    # Finaliser
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


def generate_plan_de_pose_from_calcul(calcul: Dict[str, Any], projet: Dict[str, Any]) -> BytesIO:
    """
    Génère un plan de pose à partir des données d'un calcul.

    Args:
        calcul: Données complètes du calcul
        projet: Données du projet

    Returns:
        BytesIO contenant le PDF
    """
    projet_info = {
        'name': projet.get('name', 'N/A'),
        'reference': projet.get('reference', 'N/A'),
        'client_name': projet.get('client_name', 'N/A'),
    }

    calcul_info = {
        'name': calcul.get('name', 'N/A'),
        'date': calcul.get('computed_at', datetime.now().isoformat()),
    }

    resultats = calcul.get('resultats', {})

    # Récupérer la largeur depuis les paramètres si disponible
    parametres = calcul.get('parametres', {})
    geometrie = parametres.get('geometrie', {})
    largeur = geometrie.get('largeur_plancher', 10.0)

    return generate_plan_de_pose(projet_info, calcul_info, resultats, largeur_plancher=largeur)
