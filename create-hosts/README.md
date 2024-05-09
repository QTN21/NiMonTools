# Zabbix Host Register

Script python d'auto-découverte des hotes d'un réseau client

## Requirements
- Installation du module Zabbix
```bash
pip install zabbix_utils
```

- Installation de nmap
```bash
sudo apt install nmap
```

# Exécution
1. Remplir le fichier de config

| Paramètre | Description |
|--|--|
| `ip_range`  | Liste des range IP à scanner |
| `zbx_url`   | Url du serveur web de zabbix pour envoyer les hotes |
| `token`     | Valeur du token API créé dans Zabbix |
| `secu_name` | (Optionnel si agent SNMP) identifiant pour contacter l'agent |
| `authpass`  | (Optionnel si agent SNMP) mot de passe d'authentification pour contacter l'agent |
| `privpass`  | (Optionnel si agent SNMP) mot de passe de confidentialité pour contacter l'agent |
| `group`     | Nom du groupe d'hote à créer (= identifiant des machines du réseau client) |

```json
{
    "ip_range": ["192.168.1.1/24", "192.168.2.1/24"],
    "zbx_url": "IP:PORT", 
    "token": "xxxxxxxxx", 
    "secu_name": "zbx", 
    "authpass": "zabbix_pass", 
    "privpass": "zabbix_pass", 
    "group": "TEST"
}
```

2. Lancement du script
L'exécution du script doit se faire en root afin de pouvoir lancer un scan NMAP complet
```bash
sudo python3 host_resgistration.py
```

# Visualisation de l'activité
Le script génère un fichier de log. Il peut être utile pour récupérer les hotes n'ayant pas été traité par le script (= n'ayant pas le port 161 ou 10050 ouvert)
```bash
tail ./host_resgistration.log
```