# Tests

Ce dossier contient les tests unitaires et d'intégration pour Vision Numérique.

## Structure

(À venir)

## Exécution des Tests

Pour exécuter les tests, utilisez pytest :

```bash
pip install pytest pytest-cov
pytest tests/
```

Avec couverture de code :

```bash
pytest tests/ --cov=vision_numerique --cov-report=html
```

## Écriture de Tests

Les tests doivent suivre les conventions pytest :

- Fichiers de test : `test_*.py`
- Fonctions de test : `test_*()`
- Classes de test : `Test*`

