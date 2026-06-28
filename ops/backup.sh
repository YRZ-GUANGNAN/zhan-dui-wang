#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

backup_dir=/opt/zhandui/backups
mysql_config=/etc/zhandui/backup.cnf
database=datingsite
timestamp=$(date +%Y%m%d_%H%M%S)
destination="${backup_dir}/zhandui_${timestamp}.sql.gz"
temporary="${destination}.tmp"

cleanup() {
  rm -f "$temporary"
}
trap cleanup EXIT

mkdir -p "$backup_dir"
mysqldump \
  --defaults-extra-file="$mysql_config" \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  --events \
  "$database" | gzip -9 > "$temporary"

gzip -t "$temporary"
test "$(gzip -dc "$temporary" | wc -c)" -gt 1000
mv "$temporary" "$destination"
sha256sum "$destination" > "${destination}.sha256"
find "$backup_dir" -maxdepth 1 -type f -name 'zhandui_*.sql.gz*' -mtime +14 -delete
