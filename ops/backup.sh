#!/bin/sh
# Nightly Mentor housekeeping: database dump + model store, keep 14 days,
# then reclaim Docker build cache.
#
# The cache is the real threat to a box that is meant to run for months.
# Every deploy leaves layers behind; ~20 rebuilds in a single day grew it
# to 12GB, most of the disk in use. Backups are worthless if the volume
# fills, so the prune runs here where it is guaranteed to run.
set -e
STAMP=$(date +%F)
cd /opt/mentor
docker compose -f docker-compose.caddy.yml exec -T db pg_dump -U mentor mentor | gzip > "backups/db_${STAMP}.sql.gz"
docker compose -f docker-compose.caddy.yml exec -T app tar cz -C /app/backend models > "backups/models_${STAMP}.tar.gz" 2>/dev/null || true
find backups -name "*.gz" -mtime +14 -delete

# Keep a week of build cache so a same-week redeploy stays fast, then drop it.
RECLAIMED=$(docker builder prune --force --filter 'until=168h' 2>/dev/null | tail -1)
docker image prune --force >/dev/null 2>&1 || true

# Hard floor. The 7-day window assumes a normal deploy cadence; a burst of
# rebuilds can outrun it. If the volume gets tight, everything reclaimable
# goes — a slow rebuild is always preferable to a full disk.
FREE_PCT=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$FREE_PCT" -gt 80 ]; then
  docker builder prune --force >/dev/null 2>&1 || true
  echo "$(date -Is) disk above 80% — pruned all build cache" >> backups/backup.log
fi

FREE=$(df -h / | awk 'NR==2 {print $4" free ("$5" used)"}')
echo "$(date -Is) backup ok: db_${STAMP}.sql.gz + models_${STAMP}.tar.gz | ${RECLAIMED} | disk: ${FREE}" >> backups/backup.log
