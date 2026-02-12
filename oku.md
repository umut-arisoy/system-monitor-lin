# Python3 ve pip kurulu olmalı
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 -y

# Gerekli Python paketleri
pip3 install psutil PyQt5 --break-system-packages

# Dosyayı kaydet
chmod +x system_monitor.py

python3 system_monitor.py


# Kurulum scriptini çalıştır
chmod +x install.sh
./install.sh

# Veritabanını görüntüle
sqlite3 system_monitor.db "SELECT * FROM performance_log LIMIT 10;"

# Toplam kayıt sayısı
sqlite3 system_monitor.db "SELECT COUNT(*) FROM performance_log;"

# Veritabanını sıfırla
rm system_monitor.db
