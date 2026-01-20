# ConcreteFlow - Plan de Développement

## Priorité Haute - Support Multi-Normes (Eurocode + Autres)

### Backend - Architecture des Normes
- [ ] Créer l'enum `NormeType` (EUROCODE_2, ACI_318, BAEL_91, BS_8110, CSA_A23)
- [ ] Créer le module `backend/app/services/calculs/normes/` avec une classe abstraite `NormeBase`
- [ ] Implémenter `EurocodeNorme` (norme actuelle, refactoriser depuis le code existant)
- [ ] Implémenter `ACI318Norme` (norme américaine ACI 318)
- [ ] Implémenter `BAELNorme` (ancienne norme française BAEL 91)
- [ ] Créer une factory `NormeFactory.get_norme(norme_type)` pour instancier la bonne norme

### Backend - Intégration aux Calculs
- [ ] Ajouter le champ `norme: NormeType` au modèle `Projet` (norme par défaut du projet)
- [ ] Ajouter le champ `norme: NormeType` au modèle `Calcul` (peut override le projet)
- [ ] Créer la migration Alembic pour les nouveaux champs
- [ ] Modifier les services de calcul pour utiliser `NormeFactory`
- [ ] Adapter les formules de flexion selon la norme sélectionnée
- [ ] Adapter les formules de cisaillement selon la norme
- [ ] Adapter les coefficients de sécurité selon la norme

### Frontend - Sélection de Norme
- [ ] Créer le composant `NormeSelector` (dropdown avec les normes disponibles)
- [ ] Ajouter le sélecteur de norme dans le formulaire de création de projet
- [ ] Ajouter le sélecteur de norme dans l'éditeur de calcul
- [ ] Afficher la norme utilisée dans les résultats de calcul
- [ ] Ajouter une icône/badge indiquant la norme (EC2, ACI, BAEL...)

### Documentation des Normes
- [ ] Créer `specs/normes/eurocode_ec2.md` avec les formules clés
- [ ] Créer `specs/normes/aci_318.md` avec les différences vs Eurocode
- [ ] Créer `specs/normes/bael_91.md` avec les formules françaises

## Priorité Haute - Import PDF Plans Béton Armé (Poutrelles-Hourdis)

### Backend - Extraction PDF
- [ ] Installer les dépendances PDF : `pdfplumber`, `PyPDF2`, `pdf2image`
- [ ] Installer Tesseract OCR pour les plans scannés : `pytesseract`
- [ ] Créer le service `backend/app/services/import/pdf_plan_extractor.py`
- [ ] Implémenter l'extraction de texte des PDF (tableaux, annotations)
- [ ] Implémenter l'OCR pour les PDF scannés/images
- [ ] Créer le parser pour identifier les données de plancher :
  - Portées (longueurs en mètres)
  - Types de poutrelles (références fabricant)
  - Épaisseur de dalle de compression
  - Charges (permanentes, exploitation)
  - Entre-axes des poutrelles

### Backend - API Import
- [ ] Créer l'endpoint `POST /api/v1/calculs/poutrelles/import-pdf`
- [ ] Valider le fichier PDF (taille max, format)
- [ ] Stocker le PDF original dans `uploads/plans/`
- [ ] Retourner les données extraites en JSON pour validation
- [ ] Créer l'endpoint `POST /api/v1/calculs/poutrelles/confirm-import` pour confirmer

### Backend - Analyse Intelligente du Plan
- [ ] Détecter automatiquement le format du plan (tableau, schéma, mixte)
- [ ] Extraire les cotes dimensionnelles du plan
- [ ] Identifier les références de poutrelles dans le cartouche
- [ ] Parser les tableaux de charges si présents
- [ ] Gérer les différents formats de plans (Autocad export, scan, dessin)

### Frontend - Interface Import PDF
- [ ] Créer le composant `PdfPlanUploader` avec drag & drop
- [ ] Afficher la prévisualisation du PDF uploadé (react-pdf)
- [ ] Créer le composant `ExtractedDataReview` pour valider les données
- [ ] Afficher les données extraites dans un formulaire éditable
- [ ] Permettre la correction manuelle des données mal extraites
- [ ] Ajouter un indicateur de confiance pour chaque donnée extraite
- [ ] Bouton "Lancer le calcul" après validation

### Frontend - Intégration Calcul Poutrelles
- [ ] Ajouter l'option "Importer depuis PDF" dans la page de calcul poutrelles
- [ ] Pré-remplir le formulaire de calcul avec les données extraites
- [ ] Conserver le lien vers le PDF source dans le calcul
- [ ] Afficher une miniature du plan dans les résultats

### Tests & Validation
- [ ] Créer des PDF de test (différents formats de plans)
- [ ] Tester l'extraction sur des plans réels de bureaux d'études
- [ ] Valider la précision de l'OCR sur les plans scannés
- [ ] Gérer les cas d'erreur (PDF illisible, format inconnu)

## Priorité Haute - Dashboard & Statistiques

- [ ] Créer l'endpoint API `GET /api/v1/dashboard/stats` (nombre projets, calculs, utilisateurs)
- [ ] Créer le composant `DashboardPage` dans frontend/src/pages/
- [ ] Implémenter les widgets de statistiques (cartes avec chiffres clés)
- [ ] Ajouter un graphique d'activité récente (calculs par jour/semaine)
- [ ] Intégrer le dashboard dans la navigation principale

## Priorité Haute - Export PDF/Excel

- [ ] Créer le service `backend/app/services/export/pdf_generator.py` avec ReportLab
- [ ] Créer le service `backend/app/services/export/excel_generator.py` avec openpyxl
- [ ] Ajouter l'endpoint `GET /api/v1/calculs/{id}/export?format=pdf|excel`
- [ ] Créer le template PDF pour les rapports de calcul (en-tête, résultats, conformité)
- [ ] Ajouter les boutons d'export dans l'interface frontend (CalculDetail)

## Priorité Moyenne - Gestion des Éléments de Structure

- [ ] Créer le modèle `Element` dans backend/app/models/ (poutre, poteau, dalle, etc.)
- [ ] Créer les schémas Pydantic pour Element
- [ ] Créer les endpoints CRUD pour les éléments (`/api/v1/elements`)
- [ ] Lier les éléments aux projets et aux calculs
- [ ] Créer le composant `ElementList` dans le frontend
- [ ] Créer le formulaire d'ajout/édition d'élément

## Priorité Moyenne - Amélioration des Calculs

- [ ] Ajouter la vérification des poteaux (compression + flambement)
- [ ] Ajouter le calcul des fondations superficielles
- [ ] Améliorer les messages de conformité Eurocode (plus détaillés)
- [ ] Ajouter les coefficients de sécurité configurables

## Priorité Basse - Multi-tenant

- [ ] Ajouter le middleware de tenant dans FastAPI
- [ ] Filtrer automatiquement les requêtes par tenant_id
- [ ] Ajouter la gestion des rôles (admin, ingénieur, lecteur)
- [ ] Créer la page d'administration des utilisateurs

## Priorité Basse - Améliorations UX

- [ ] Ajouter la pagination sur les listes (projets, calculs)
- [ ] Implémenter la recherche/filtrage sur les listes
- [ ] Ajouter des notifications toast pour les actions (succès/erreur)
- [ ] Améliorer le responsive design pour mobile

## Completed

- [x] Authentification (inscription, connexion, JWT)
- [x] Gestion de projets (CRUD, statuts)
- [x] Calculs structurels de base (flexion, flèche, effort tranchant)
- [x] Calcul plancher poutrelles-hourdis
- [x] Import fichiers DXF
- [x] Visualisation canvas (Konva)
- [x] Gestion des fabricants
- [x] Import cahiers de portées

## Corrections de Bugs

- [ ] (Ajouter ici les bugs découverts pendant le développement)

---

## Notes de Progression

### Dernière mise à jour
- Date: (à mettre à jour par Ralph)
- Dernière tâche complétée: (à mettre à jour par Ralph)

### Découvertes & Décisions
- (Ralph ajoutera ici les découvertes importantes)
