#!/bin/bash

set -euo pipefail

DATE=$(date +%Y%m%d_%H%M)
FILE_BACK="backup_mon_$DATE.tar.gz"

DIR_LOKI="/tmp/loki"
DIR_BACK="/home/zabbix/backup/"

DB_ZABBIX="zabbix-db"
DB_GRAFANA="grafana-db"
DB_USER="zabbix"

SRV_ZABBIX="zabbix-server"
SRV_GRAFANA="grafana-server"
SRV_LOKI="loki-server"

backup() {
    # Backup DB
    docker exec "$DB_ZABBIX" pg_dump -U "$DB_USER" zabbix > "$DB_ZABBIX.sql"
    docker exec -i "$DB_GRAFANA" pg_dump -U "$DB_USER" grafana > "$DB_GRAFANA.sql"

    # Backup directory
    docker cp "$SRV_ZABBIX:/var/lib/zabbix" $SRV_ZABBIX
    docker cp "$SRV_GRAFANA:/var/lib/grafana" $SRV_GRAFANA
    docker cp "$SRV_LOKI:$DIR_LOKI" $SRV_LOKI
}

# Do the backup
backup

# Store the backup
tar cvzf $FILE_BACK "$DB_ZABBIX.sql" "$DB_GRAFANA.sql" $SRV_ZABBIX $SRV_GRAFANA $SRV_LOKI
sha256sum $FILE_BACK >> $DIR_BACK/backup.hash

# Remove files
if [[ "$?" -eq 0 ]]; then
    mv $FILE_BACK "$DIR_BACK"
    rm -rf "$DB_ZABBIX.sql" "$DB_GRAFANA.sql" $SRV_ZABBIX $SRV_GRAFANA $SRV_LOKI
fi

echo "BACKUP ENDED"