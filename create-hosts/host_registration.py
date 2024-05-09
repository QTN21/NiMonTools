from zabbix_utils import ZabbixAPI
import subprocess
import logging
import re
import json

logging.basicConfig(filename='./host_registration.log', filemode='a', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
reg_net_scan = re.compile(r"Nmap scan report for.* \(?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)?\nHost is up \([0-9.]+s latency\)\.\n\nPORT\s+STATE\s+SERVICE\n10050\/tcp\s+([\w|]+)\s+zabbix-agent\n161\/udp\s+([\w|]+)\s+snmp")


def scan_ip(range):
    """
    Fonction de scan du réseau et retourne un dictionnaire "IP:PORT"
    range: liste des range IP à scanner (ex : ["192.168.1.1/24", "192.168.2.1/24"])
    return: un dictionnaire {ip: [port, ouvert]}
    """
    ITEM_DIC = {}
    command = ["nmap", "-sU", "-sS", "-p", "U:161,T:10050"]

    # Si la variable range contient plusieurs range IP
    for i in range:
        command.append(i)

    # Lancement du scan réseau
    scan = subprocess.run(command, shell=False, capture_output=True, text=True)

    if scan.returncode == 0:
        info_group = reg_net_scan.findall(scan.stdout)
        
        for item in info_group:
            ip_addr, zabbix_status, snmp_status = item[0], item[1], item[2]
            ITEM_DIC[ip_addr] = []

            if snmp_status == "open": ITEM_DIC[ip_addr].append(161)

            if zabbix_status == "open": ITEM_DIC[ip_addr].append(10050)

        logging.info("Network discovery passed successfully")
        return ITEM_DIC
    else:
        logging.error("Network discovery encountered an error")
        exit(1)


def zbx_session(url, token):
    """
    Fonction créant une session en lien avec le serveur Zabbix
    url    : URL zabbix à contacter
    user   : utilisateur se connectant au compte zabbix
    passwd : mot de passe de l'utilisateur
    return : retourne la session et le jeton de session
    """
    try:
        zapi = ZabbixAPI(url=url, token=token)
        logging.info("Zabbix connection established")
    except:
        logging.error("Can't connect to the zabbix server")
        exit(1)
    return zapi


def get_hostgroup(zbxobj):
    """
    Fonction récupérant les noms des hostgroup déjà présent sur le serveur
    zbxobj : object de connexion zabbixAPI
    return : liste des nom de groupe
    """
    try:
        hg = zbxobj.hostgroup.get(output=["name"])
        hg = [i["name"] for i in hg]
        logging.info("Got the hostgroup name")
    except:
        logging.error("Can't get hotgroups list")
        exit(1)
    return hg


def get_host(zbxobj):
    """
    Fonction récupérant les noms des hotes déjà présent sur le serveur
    zbxobj : object de connexion zabbixAPI
    return : liste des nom d'hotes
    """
    try:
        h = zbxobj.host.get(output=["name"])
        h = [i["name"] for i in h]
        logging.info("Got the host name")
    except:
        logging.error("Can't get host list")
        exit(1)
    return h


def get_proxy(zbxobj):
    """
    Fonction récupérant les IP et id associés déjà présent sur le serveur
    zbxobj : object de connexion zabbixAPI
    return : liste des nom de groupe
    """
    try:
        p = zbxobj.proxy.get(output=["proxyid"], selectInterface=["ip"])
        p = {i["interface"]["ip"]: i["proxyid"] for i in p}
        logging.info("Got the proxy information")
    except:
        logging.error("Can't get the proxy information")
        exit(1)
    return p


def detect_proxy(dict_proxy):
    """
    Fonction détectant automatiquement l'id du proxy lié au serveur à partir de l'IP du proxy (sur lequel le script est exécuté le script)
    dict_proxy : dictionnaire contenant l'IP du proxy et l'id associé présent sur le serveur Zabbix
    return : ID du proxy concerné
    """
    # Récupération de l'adresse IP proxy
    command = "ip addr show wg0 | grep inet | awk '{print $2}' | awk -F '/' '{print $1}'"
    ip_addr = subprocess.run(command, shell=True, capture_output=True, text=True).stdout[0:-1] # [0:-1] retire le \n
    logging.info("Got the IP from WG0 interface")

    ip_proxy = [i for i in dict_proxy.keys()]
    
    if ip_addr in ip_proxy:
        # lance une requête pour récupérer l'id du proxy
        try:
            id_proxy = dict_proxy[ip_addr]
            logging.info("Proxy detected")
            return id_proxy
        except:
            logging.error("Error during getting the proxy id")
            exit(1)
    logging.error("Can't detect the proxy and return the id")


def create_hg(zbxobj, hg_list, hgname):
    """
    Fonction détectant si le hostgroup existe sinon le créer
    zbxobj : objet de connexion ZabbixAPI
    hg_list : liste des noms des hostgroup présent sur le serveur
    hgname : nom de groupe à ajouter
    return : l'id du group créé ou existant
    """
    # check if host group already exist on server
    if hgname not in hg_list:
        try:
            hg = zbxobj.hostgroup.create({'name':hgname})['groupids']
            logging.info(f"Created hostgroup {hgname} successfully")
            return hg
        except:
            logging.error(f"Can't create the hostgroup {hgname}")
            return 0
    else:
        hg = zbxobj.hostgroup.get(filter={'name': hgname})[0]["groupid"]
        logging.info(f"Host group {hgname} already exist")
        return hg


def create_host(zbxobj, dico_scan, dico_config):
    """
    Fonction de création d'hotes à partir des infos récupérées précédemment
    zbxobj : objet de connexion ZabbixAPI
    dico_scan : dictionnaire contenant les éléments d'analyse lors du scan NMAP
    dico_config : dictionnaire contenant la config du fichier CONFIG.json
    return : / 
    """
    # Check if group -> return id
    hg_list = get_hostgroup(zbxobj)
    hg_id = create_hg(zbxobj, hg_list, dico_config["group"])

    # Check and detect the proxy id
    p_list = get_proxy(zbxobj)
    p_id = detect_proxy(p_list)

    # get the existing host list
    h_list = get_host(zbxobj)

    for ip in dico_scan.keys():
        port = dico_scan[ip]
        hostname = f"{dico_config['group']}-{ip}"

        if not port:
            logging.warning(f"Host {ip} not created on zabbix server -> MUST BE CONFIGURED")

        # Check if hostname exist in zabbix
        if hostname not in h_list:
            if 161 in port:
                secuname = dico_config["secu_name"]
                authpass = dico_config["authpass"]
                privpass = dico_config["privpass"]
                try:
                    zbxobj.host.create(host=hostname, interfaces=[{"type": 2,"main": 1,"useip": 1,"ip": ip,"dns": "","port": "161","details": {"version": 3,"bulk": 0,"securityname": secuname,"contextname": "","securitylevel": 2,"authpassphrase": authpass,"privpassphrase": privpass,"authprotocol": 1,"privprotocol": 1}}], groups=[{"groupid": hg_id}], proxy_hostid=p_id)
                    logging.info(f"Host SNMP {hostname} created successfully")
                except:
                    logging.error(f"Host SNMP {hostname} encountered probleme during creation")

            if 10050 in port:
                try:
                    zbxobj.host.create(host=hostname,interfaces=[{"type": 1,"ip": ip,"dns": "","port": "10050","useip": 1,"main": 1}], groups=[{"groupid": hg_id}],proxy_hostid=p_id)
                    logging.info(f"Host Zabbix {hostname} created successfully")
                except:
                    logging.error(f"Host Zabbix {hostname} encountered probleme during creation")
        else:
            logging.info(f"Host {hostname} already exists on server")


if __name__ == "__main__":
    config = {}

    # Chargement du fichier config
    logging.info("Trying to open the configuration file")
    with open("./CONFIG.json", "r") as f:
        config = json.load(f)
        logging.info("Configuration file loaded successfully")

    # Lance la découverte du réseau et récupère les infos utiles
    logging.info("Running the IP scan")
    host_scan = scan_ip(config["ip_range"])

    # Etablissement de la connxion à Zabbix
    logging.info("Making the connection with Zabbix server")
    zapi = zbx_session(config["zbx_url"], config["token"])
    
    # Lance la création d'hotes 
    logging.info("Running the creation host")
    item_mon = create_host(zapi, host_scan, config)