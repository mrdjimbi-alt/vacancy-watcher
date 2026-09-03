#!/usr/bin/env bash
# Разворачивает сборщик вакансий на сервере с systemd.
# Запускать от root: bash install.sh
set -euo pipefail

APP_DIR=/opt/vacancy-watcher
APP_USER=vacancy
REPO=https://github.com/mrdjimbi-alt/vacancy-watcher.git

echo "==> пользователь $APP_USER"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"

echo "==> код в $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO" "$APP_DIR"
fi

echo "==> зависимости"
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "!! впиши токен и канал в $APP_DIR/.env, потом перезапусти таймер"
fi

touch /var/log/vacancy-watcher.log
chown -R "$APP_USER:$APP_USER" "$APP_DIR" /var/log/vacancy-watcher.log
chmod 600 "$APP_DIR/.env"

echo "==> systemd"
cp "$APP_DIR/deploy/vacancy-watcher.service" /etc/systemd/system/
cp "$APP_DIR/deploy/vacancy-watcher.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now vacancy-watcher.timer

echo
echo "готово. проверить:"
echo "  systemctl list-timers vacancy-watcher.timer"
echo "  systemctl start vacancy-watcher.service   # прогнать прямо сейчас"
echo "  tail -f /var/log/vacancy-watcher.log"
