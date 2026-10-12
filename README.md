# Claros AI

Site vitrine statique de Claros AI (une seule page HTML, sans build).

Déploiement : importer ce dépôt sur Vercel, framework « Other », sans commande de build. Chaque push sur `main` redéploie le site.

## Version anglaise

`en.html` (servie sur `/en`) est générée à partir de `index.html` :

```
python3 tools/build_en.py
```

Les traductions sont dans `tools/en.py`. Après toute modification du texte français, ajouter la traduction correspondante puis relancer le script : il signale les textes français restants.
