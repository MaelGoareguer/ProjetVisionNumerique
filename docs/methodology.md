# Méthodologie de Recherche

## Contexte et Motivation

Ce projet explore l'utilisation de la vision par ordinateur pour créer une interface de contrôle vidéo basée sur les gestes de la main. L'objectif est de développer un système robuste et performant capable de reconnaître différents gestes en temps réel et de les traduire en commandes de contrôle vidéo.

## État de l'Art

### Détection de Gestes de la Main

La détection et la reconnaissance de gestes de la main constituent un domaine actif de recherche en vision par ordinateur. Les approches modernes se divisent en deux catégories principales :

1. **Méthodes basées sur des modèles 3D** : Utilisent des modèles de main 3D pour estimer la pose
2. **Méthodes basées sur l'apprentissage profond** : Utilisent des réseaux de neurones pour la détection et la classification

### MediaPipe Hands

MediaPipe Hands est une solution développée par Google qui offre une détection en temps réel des landmarks de la main. Elle utilise un modèle d'apprentissage profond optimisé pour fonctionner sur CPU, permettant une détection à faible latence.

**Avantages** :
- Détection en temps réel (< 100ms de latence)
- Fonctionne sur CPU (pas besoin de GPU)
- Open source et bien documenté
- Support multi-mains

**Limitations** :
- Sensibilité aux conditions d'éclairage
- Performance dépendante de la distance main-caméra
- Modèle pré-entraîné (non personnalisable facilement)

## Approche Méthodologique

### 1. Détection des Landmarks

MediaPipe Hands détecte 21 landmarks par main, correspondant aux articulations et extrémités des doigts :

- **Poignet** : 1 point
- **Pouce** : 4 points (CMC, MCP, IP, TIP)
- **Index** : 4 points (MCP, PIP, DIP, TIP)
- **Majeur** : 4 points (MCP, PIP, DIP, TIP)
- **Annulaire** : 4 points (MCP, PIP, DIP, TIP)
- **Auriculaire** : 4 points (MCP, PIP, DIP, TIP)

Ces landmarks sont fournis en coordonnées normalisées (0-1) par rapport à l'image.

### 2. Classification des Gestes

La classification des gestes repose sur l'analyse géométrique des landmarks. Chaque geste est défini par des règles géométriques spécifiques.

#### Main Plate (Play/Pause et Plein Écran)

**Détection** :
- Nombre de doigts tendus ≥ 4 (index, majeur, annulaire, auriculaire)
- Les doigts doivent être tendus (tip.y < pip.y pour chaque doigt)

**Distinction Serrée/Écartée** :
- Calcul de la distance moyenne entre les extrémités des doigts
- Normalisation par la taille de la main (distance poignet-index MCP)
- Seuil : 42% de la taille de la main
  - < 42% → Main plate serrée (Play/Pause)
  - ≥ 42% → Main plate écartée (Plein écran)

**Formule** :
```
distance_moyenne = (d(index_tip, middle_tip) + d(middle_tip, ring_tip) + d(ring_tip, pinky_tip)) / 3
taille_main = d(wrist, index_mcp)
spread_normalized = distance_moyenne / taille_main
```

#### Navigation (Avancer/Reculer)

**Détection** :
- Index tendu (distance tip-pip > 0.05)
- Direction principalement horizontale (ratio horizontal/vertical > 0.8)
- Amplitude minimale : 0.07 (normalisé)

**Classification** :
- `index_tip.x - wrist.x > 0` → Reculer (inversé car caméra miroir)
- `index_tip.x - wrist.x < 0` → Avancer

#### Volume (Haut/Bas)

**Détection** :
- Index tendu
- Direction principalement verticale (ratio vertical/horizontal > 1.5)
- Amplitude minimale : 0.10 (normalisé)

**Classification** :
- `index_tip.y - wrist.y < 0` → Volume Up
- `index_tip.y - wrist.y > 0` → Volume Down

### 3. Optimisations de Performance

#### Traitement Alterné

Pour améliorer les performances, le système traite une frame sur deux avec MediaPipe. Les frames intermédiaires réutilisent les résultats précédents. Cette approche est valide car MediaPipe utilise déjà un système de tracking entre les frames.

```python
if frame_counter % 2 == 0 or last_results is None:
    results = hands.process(frame_rgb)
    last_results = results
else:
    results = last_results
```

#### Cache des Résultats

Les résultats de détection sont mis en cache pour éviter les recalculs inutiles.

#### Modèle Léger

Utilisation de MediaPipe Hands avec `model_complexity=0` (modèle léger) pour optimiser les performances CPU.

### 4. Système de Métriques

#### Métriques de Détection

- **Taux de détection** : Pourcentage de frames où une main est détectée
- **Taux de vrais positifs** : Pourcentage de frames avec main présente et détectée
- **Taux de faux positifs** : Pourcentage de frames sans main mais détectée

#### Métriques de Reconnaissance

- **Précision par geste** : Pourcentage de prédictions correctes pour chaque geste
- **Matrice de confusion** : Tableau croisé des gestes réels vs prédits

#### Vérité Terrain

Le système permet l'annotation manuelle de la vérité terrain :
- **H** : Main présente
- **N** : Pas de main
- **C** : Réinitialiser

Les gestes peuvent également être déclarés manuellement via des raccourcis clavier pour l'évaluation.

## Évaluation Expérimentale

### Protocole d'Évaluation

1. **Collecte de données** : Enregistrement de sessions avec différents gestes
2. **Annotation** : Marquage manuel de la vérité terrain
3. **Calcul des métriques** : Analyse automatique via le module Metrics
4. **Visualisation** : Génération de matrices de confusion et graphiques

### Métriques de Performance

- **Précision** : Capacité à détecter correctement les gestes
- **Rappel** : Capacité à ne pas manquer de gestes
- **Latence** : Temps de traitement par frame
- **FPS** : Images par seconde traitées

## Limitations et Défis

### Limitations Actuelles

1. **Conditions d'éclairage** : Performance dégradée en faible luminosité
2. **Distance main-caméra** : Nécessite une distance optimale (30-80 cm)
3. **Occlusions** : Difficulté avec les mains partiellement cachées
4. **Variations inter-individuelles** : Taille et forme des mains variables

### Défis Techniques

1. **Robustesse** : Améliorer la robustesse aux variations d'environnement
2. **Latence** : Réduire la latence pour une interaction plus fluide
3. **Précision** : Améliorer la précision de reconnaissance des gestes complexes
4. **Scalabilité** : Support de plus de gestes et de mains simultanées

## Travaux Futurs

### Améliorations Proposées

1. **Deep Learning** : Intégration d'un modèle de classification par deep learning
2. **Calibration automatique** : Adaptation automatique des seuils selon l'utilisateur
3. **Multi-mains avancé** : Support de gestes impliquant plusieurs mains
4. **Apprentissage continu** : Adaptation du modèle aux gestes de l'utilisateur

### Directions de Recherche

1. **Fusion multi-modalité** : Combinaison vision + audio pour améliorer la robustesse
2. **Gestion de l'ambiguïté** : Système de confiance pour les gestes ambigus
3. **Personnalisation** : Adaptation aux préférences et capacités de l'utilisateur

## Références

- Lugaresi, C., et al. (2019). "MediaPipe: A Framework for Building Perception Pipelines"
- MediaPipe Hands Documentation: https://google.github.io/mediapipe/solutions/hands
- Zhang, F., et al. (2020). "MediaPipe Hands: On-device Real-time Hand Tracking"

