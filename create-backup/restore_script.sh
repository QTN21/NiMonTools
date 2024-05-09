#!/bin/bash

set -euo pipefail

FILE_BACKUP="backup_mon_20240426_1247.tar.gz"
FILE_COMPOSE="./zbx-utility/create-server/docker-compose.yml"

DIR_RESTORE="./restore"
DIR_LOKI="/tmp/loki"

DB_ZABBIX="zabbix-db"
DB_GRAFANA="grafana-db"
DB_USER="zabbix"

SRV_ZABBIX="zabbix-server"
SRV_GRAFANA="grafana-server"
SRV_LOKI="loki-server"

restore () {
    docker compose -f $FILE_COMPOSE down

    # restore db
    docker compose -f $FILE_COMPOSE up -d $DB_ZABBIX $DB_GRAFANA
    echo "Restoring the databases"
    docker cp $DIR_RESTORE/$DB_ZABBIX.sql $DB_ZABBIX:/tmp/$DB_ZABBIX.sql
    docker exec $DB_ZABBIX /bin/bash -c "dropdb -U $DB_USER zabbix && createdb -U $DB_USER zabbix && psql -U $DB_USER zabbix < /tmp/$DB_ZABBIX.sql"

    docker cp $DIR_RESTORE/$DB_GRAFANA.sql $DB_GRAFANA:/tmp/$DB_GRAFANA.sql
    docker exec $DB_GRAFANA /bin/bash -c "dropdb -U $DB_USER grafana && createdb -U $DB_USER grafana && psql -U $DB_USER grafana < /tmp/$DB_GRAFANA.sql"

    docker compose -f $FILE_COMPOSE down

    # restore directory
    docker compose -f $FILE_COMPOSE up -d $SRV_LOKI $SRV_ZABBIX $SRV_GRAFANA
    echo "Restoring the servers directory"
    docker cp "$DIR_RESTORE/$SRV_ZABBIX" $SRV_ZABBIX:/var/lib/zabbix
    docker cp "$DIR_RESTORE/$SRV_GRAFANA" $SRV_GRAFANA:/var/lib/grafana
    docker cp "$DIR_RESTORE/$SRV_LOKI" $SRV_LOKI:$DIR_LOKI

    docker compose -f $FILE_COMPOSE down
}

mkdir $DIR_RESTORE
tar xzf $FILE_BACKUP -C $DIR_RESTORE
restore
rm -rf $DIR_RESTORE