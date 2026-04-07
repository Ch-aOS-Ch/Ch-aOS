if [ "$(id -u)" -ne 0 ]; then
  echo "This script requires superuser (root) privileges."
  echo "Please run it with 'sudo' or as root."
  exit 1
fi

rm -rf /opt/chaos-app/
rm -rf /usr/bin/chaos
