# Installation du webhook pour NXWitness

# Importation du webhook
```bash
cd /opt
git clone https://github.com/QTN21/nxwebhook.git
```

## Build du Dockerfile
```bash
docker build -t nxwebhook .
```

## Lancement du conteneur
```bash
docker run --rm -d -p 5000:5000 -v $(pwd):/app nxwebhook:latest
```
