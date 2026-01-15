"""
Générateur de notes de calcul PDF.
Utilise ReportLab pour créer des documents PDF professionnels.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from typing import Dict, Any, List, Optional
from datetime import datetime
from io import BytesIO
import os


class PDFGenerator:
    """Générateur de documents PDF pour ConcreteFlow."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configure les styles personnalisés."""
        # Titre principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e40af')
        ))

        # Sous-titre
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=colors.HexColor('#1e40af')
        ))

        # Section
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#374151')
        ))

        # Corps de texte
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))

        # Formule
        self.styles.add(ParagraphStyle(
            name='Formula',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Courier',
            spaceAfter=4,
            spaceBefore=4,
            leftIndent=20
        ))

        # Résultat OK
        self.styles.add(ParagraphStyle(
            name='ResultOK',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#059669')
        ))

        # Résultat NOK
        self.styles.add(ParagraphStyle(
            name='ResultNOK',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#dc2626')
        ))

    def generate(
        self,
        calcul: Dict[str, Any],
        projet: Dict[str, Any] = None,
        company_info: Dict[str, Any] = None
    ) -> bytes:
        """
        Génère une note de calcul PDF.

        Args:
            calcul: Données du calcul avec paramètres et résultats
            projet: Informations du projet (optionnel)
            company_info: Informations de l'entreprise (optionnel)

        Returns:
            Contenu PDF en bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Construire le contenu
        story = []

        # En-tête
        story.extend(self._build_header(calcul, projet, company_info))

        # Données d'entrée
        story.extend(self._build_input_section(calcul))

        # Résultats détaillés
        story.extend(self._build_results_section(calcul))

        # Synthèse ferraillage
        story.extend(self._build_reinforcement_section(calcul))

        # Conclusion
        story.extend(self._build_conclusion(calcul))

        # Pied de page avec signature
        story.extend(self._build_footer())

        # Générer le PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _build_header(
        self,
        calcul: Dict,
        projet: Dict = None,
        company_info: Dict = None
    ) -> List:
        """Construit l'en-tête du document."""
        elements = []

        # Titre
        elements.append(Paragraph(
            "NOTE DE CALCUL",
            self.styles['MainTitle']
        ))

        # Informations générales
        info_data = [
            ["Référence:", calcul.get('name', 'N/A')],
            ["Type:", self._get_type_label(calcul.get('type_produit', ''))],
            ["Norme:", calcul.get('norme', 'EC2')],
            ["Date:", datetime.now().strftime("%d/%m/%Y")],
        ]

        if projet:
            info_data.insert(0, ["Projet:", projet.get('name', 'N/A')])
            info_data.insert(1, ["Client:", projet.get('client_name', 'N/A')])

        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10*mm))

        # Ligne de séparation
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e5e7eb')
        ))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_input_section(self, calcul: Dict) -> List:
        """Construit la section des données d'entrée."""
        elements = []
        params = calcul.get('parametres', {})

        elements.append(Paragraph("1. DONNÉES D'ENTRÉE", self.styles['SubTitle']))

        # Géométrie
        elements.append(Paragraph("1.1 Géométrie", self.styles['SectionTitle']))
        geom = params.get('geometrie', {})
        geom_data = [
            ["Paramètre", "Valeur", "Unité"],
            ["Portée", str(geom.get('portee', '-')), "m"],
            ["Largeur", str(geom.get('largeur', '-')), "m"],
            ["Hauteur", str(geom.get('hauteur', '-')), "m"],
        ]
        elements.append(self._create_table(geom_data))
        elements.append(Spacer(1, 5*mm))

        # Charges
        elements.append(Paragraph("1.2 Charges", self.styles['SectionTitle']))
        charges = params.get('charges', {})
        charges_data = [
            ["Charge", "Valeur", "Unité"],
            ["Permanentes (G)", str(charges.get('permanentes', '-')), "kN/m²"],
            ["Exploitation (Q)", str(charges.get('exploitation', '-')), "kN/m²"],
        ]
        elements.append(self._create_table(charges_data))
        elements.append(Spacer(1, 5*mm))

        # Combinaisons
        g = charges.get('permanentes', 0)
        q = charges.get('exploitation', 0)
        elements.append(Paragraph("1.3 Combinaisons de charges", self.styles['SectionTitle']))
        elements.append(Paragraph(
            f"ELU: 1.35×G + 1.5×Q = 1.35×{g} + 1.5×{q} = {1.35*g + 1.5*q:.2f} kN/m²",
            self.styles['Formula']
        ))
        elements.append(Paragraph(
            f"ELS: G + Q = {g} + {q} = {g+q:.2f} kN/m²",
            self.styles['Formula']
        ))
        elements.append(Spacer(1, 5*mm))

        # Matériaux
        elements.append(Paragraph("1.4 Matériaux", self.styles['SectionTitle']))
        mats = params.get('materiaux', {})
        mats_data = [
            ["Matériau", "Classe", "Caractéristique"],
            ["Béton", mats.get('classe_beton', 'C30/37'), "fck = 30 MPa"],
            ["Acier", mats.get('classe_acier', 'S500'), "fyk = 500 MPa"],
        ]
        elements.append(self._create_table(mats_data))
        elements.append(Spacer(1, 10*mm))

        return elements

    def _build_results_section(self, calcul: Dict) -> List:
        """Construit la section des résultats."""
        elements = []
        resultats = calcul.get('resultats', {})

        elements.append(Paragraph("2. RÉSULTATS DES VÉRIFICATIONS", self.styles['SubTitle']))

        # Flexion
        if 'flexion' in resultats:
            elements.extend(self._build_flexion_results(resultats['flexion']))

        # Flèche
        if 'fleche' in resultats:
            elements.extend(self._build_fleche_results(resultats['fleche']))

        # Effort tranchant
        if 'effort_tranchant' in resultats:
            elements.extend(self._build_shear_results(resultats['effort_tranchant']))

        return elements

    def _build_flexion_results(self, flexion: Dict) -> List:
        """Section résultats flexion."""
        elements = []
        elements.append(Paragraph("2.1 Vérification en flexion", self.styles['SectionTitle']))

        # Moment
        elements.append(Paragraph(
            f"Moment fléchissant ELU: MEd = {flexion.get('moment_elu_kNm', 0):.2f} kN.m",
            self.styles['BodyText']
        ))
        elements.append(Paragraph(
            f"Moment fléchissant ELS: Mser = {flexion.get('moment_els_kNm', 0):.2f} kN.m",
            self.styles['BodyText']
        ))

        # Moment réduit
        elements.append(Paragraph(
            f"Moment réduit: μ = {flexion.get('mu', 0):.4f} < μlim = {flexion.get('mu_limite', 0.372):.4f}",
            self.styles['Formula']
        ))

        # Section d'acier
        elements.append(Paragraph(
            f"Section d'acier requise: As = {flexion.get('as_final_cm2', 0):.2f} cm²",
            self.styles['BodyText']
        ))
        elements.append(Paragraph(
            f"(As,min = {flexion.get('as_min_cm2', 0):.2f} cm², As,max = {flexion.get('as_max_cm2', 0):.2f} cm²)",
            self.styles['BodyText']
        ))

        # Verdict
        ok = flexion.get('verification_ok', False)
        style = self.styles['ResultOK'] if ok else self.styles['ResultNOK']
        verdict = "VÉRIFIÉ" if ok else "NON VÉRIFIÉ"
        elements.append(Paragraph(f"→ Flexion: {verdict}", style))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_fleche_results(self, fleche: Dict) -> List:
        """Section résultats flèche."""
        elements = []
        elements.append(Paragraph("2.2 Vérification de la flèche", self.styles['SectionTitle']))

        elements.append(Paragraph(
            f"Flèche calculée: f = {fleche.get('fleche_totale_mm', 0):.2f} mm",
            self.styles['BodyText']
        ))
        elements.append(Paragraph(
            f"Flèche limite (L/250): flim = {fleche.get('fleche_limite_mm', 0):.2f} mm",
            self.styles['BodyText']
        ))

        # Verdict
        ok = fleche.get('verification_ok', False)
        style = self.styles['ResultOK'] if ok else self.styles['ResultNOK']
        verdict = "VÉRIFIÉ" if ok else "NON VÉRIFIÉ"
        elements.append(Paragraph(f"→ Flèche: {verdict}", style))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_shear_results(self, shear: Dict) -> List:
        """Section résultats effort tranchant."""
        elements = []
        elements.append(Paragraph("2.3 Vérification de l'effort tranchant", self.styles['SectionTitle']))

        elements.append(Paragraph(
            f"Effort tranchant sollicitant: VEd = {shear.get('effort_tranchant_kN', 0):.2f} kN",
            self.styles['BodyText']
        ))
        elements.append(Paragraph(
            f"Résistance sans armatures: VRd,c = {shear.get('resistance_sans_armatures_kN', 0):.2f} kN",
            self.styles['BodyText']
        ))

        if shear.get('besoin_armatures_transversales'):
            elements.append(Paragraph(
                f"Armatures transversales requises: Asw/s = {shear.get('as_transversal_cm2_m', 0):.2f} cm²/m",
                self.styles['BodyText']
            ))

        # Verdict
        ok = shear.get('verification_ok', False)
        style = self.styles['ResultOK'] if ok else self.styles['ResultNOK']
        verdict = "VÉRIFIÉ" if ok else "NON VÉRIFIÉ"
        elements.append(Paragraph(f"→ Effort tranchant: {verdict}", style))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_reinforcement_section(self, calcul: Dict) -> List:
        """Section ferraillage."""
        elements = []
        resultats = calcul.get('resultats', {})
        ferraillage = resultats.get('ferraillage', {})

        if not ferraillage:
            return elements

        elements.append(Paragraph("3. FERRAILLAGE", self.styles['SubTitle']))

        ferr_data = [["Position", "Désignation"]]

        if ferraillage.get('armatures_inferieures', {}).get('designation'):
            ferr_data.append([
                "Armatures inférieures",
                ferraillage['armatures_inferieures']['designation']
            ])

        if ferraillage.get('armatures_superieures', {}).get('designation'):
            ferr_data.append([
                "Armatures supérieures",
                ferraillage['armatures_superieures']['designation']
            ])

        if ferraillage.get('armatures_transversales', {}).get('designation'):
            ferr_data.append([
                "Cadres / Étriers",
                ferraillage['armatures_transversales']['designation']
            ])

        if len(ferr_data) > 1:
            elements.append(self._create_table(ferr_data))

        elements.append(Spacer(1, 10*mm))
        return elements

    def _build_conclusion(self, calcul: Dict) -> List:
        """Section conclusion."""
        elements = []
        resultats = calcul.get('resultats', {})
        summary = resultats.get('summary', {})

        elements.append(Paragraph("4. CONCLUSION", self.styles['SubTitle']))

        global_ok = summary.get('verification_globale') == 'OK'

        if global_ok:
            elements.append(Paragraph(
                "Toutes les vérifications sont satisfaites. "
                "L'élément est conforme aux exigences de l'Eurocode 2.",
                self.styles['ResultOK']
            ))
        else:
            elements.append(Paragraph(
                "Certaines vérifications ne sont pas satisfaites. "
                "Des modifications sont nécessaires.",
                self.styles['ResultNOK']
            ))

        elements.append(Spacer(1, 10*mm))
        return elements

    def _build_footer(self) -> List:
        """Pied de page."""
        elements = []

        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e5e7eb')
        ))
        elements.append(Spacer(1, 5*mm))

        elements.append(Paragraph(
            f"Document généré par ConcreteFlow le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#6b7280'),
                alignment=TA_CENTER
            )
        ))

        return elements

    def _create_table(self, data: List[List], col_widths: List = None) -> Table:
        """Crée un tableau formaté."""
        if col_widths is None:
            col_widths = [5*cm, 4*cm, 3*cm][:len(data[0])]

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            # Bordures
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            # Alignement
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _get_type_label(self, type_produit: str) -> str:
        """Retourne le libellé du type de produit."""
        labels = {
            'poutrelle': 'Poutrelle précontrainte',
            'predalle': 'Prédalle',
            'dalle_alveolaire': 'Dalle alvéolaire',
            'poutre': 'Poutre béton armé',
            'dalle_pleine': 'Dalle pleine',
        }
        return labels.get(type_produit, type_produit)


def generate_note_calcul(
    calcul: Dict[str, Any],
    projet: Dict[str, Any] = None,
    company_info: Dict[str, Any] = None
) -> bytes:
    """
    Fonction utilitaire pour générer une note de calcul PDF.

    Args:
        calcul: Données du calcul
        projet: Données du projet (optionnel)
        company_info: Informations entreprise (optionnel)

    Returns:
        Contenu PDF en bytes
    """
    generator = PDFGenerator()
    return generator.generate(calcul, projet, company_info)
