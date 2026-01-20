# ConcreteFlow - Plan de Développement

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
