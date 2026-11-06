#!/usr/bin/env bash
# Instalacion en Raspberry Pi OS (Lite o Desktop). Uso: sudo bash raspberry/install.sh
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Ejecuta con sudo"; exit 1; }
SRC="$(cd "$(dirname "$0")/.." && pwd)"

apt-get update
apt-get install -y nginx python3-venv

mkdir -p /opt/reloj /var/www/reloj
python3 -m venv /opt/reloj/venv
/opt/reloj/venv/bin/pip install -r "$SRC/requirements.txt"
cp "$SRC/spider.py" /opt/reloj/spider.py
cp "$SRC/docs/index.html" /var/www/reloj/index.html

# Clave de API: edita /etc/reloj.env y pon tu clave despues de OPENROUTER_API_KEY=
if [ ! -f /etc/reloj.env ]; then
  printf 'OPENROUTER_API_KEY=\nOPENROUTER_MODEL=openai/gpt-4o-mini\nDATA_PATH=/var/www/reloj/data.json\n' > /etc/reloj.env
fi
chown root:www-data /etc/reloj.env && chmod 640 /etc/reloj.env

cat > /opt/reloj/run.sh <<'EOS'
#!/usr/bin/env bash
set -a; . /etc/reloj.env; set +a
exec /opt/reloj/venv/bin/python /opt/reloj/spider.py
EOS
chmod +x /opt/reloj/run.sh

touch /var/log/reloj.log && chown www-data:www-data /var/log/reloj.log
chown -R www-data:www-data /var/www/reloj
echo '0 6 * * * www-data /opt/reloj/run.sh >> /var/log/reloj.log 2>&1' > /etc/cron.d/reloj

cp "$SRC/raspberry/nginx-reloj.conf" /etc/nginx/sites-available/reloj
ln -sf /etc/nginx/sites-available/reloj /etc/nginx/sites-enabled/reloj
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "Listo. 1) Edita /etc/reloj.env con tu OPENROUTER_API_KEY."
echo "2) Primera corrida: sudo -u www-data /opt/reloj/run.sh"
echo "3) Abre http://$(hostname -I | awk '{print $1}')/ desde tu red."
