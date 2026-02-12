#!/bin/bash
# Kali Linux Sistem Monitörü Kurulum Scripti

echo "================================"
echo "Sistem Monitörü Kurulum Scripti"
echo "================================"
echo ""

# Root kontrolü
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Bu scripti root olarak çalıştırmayın!"
    echo "Normal kullanıcı ile çalıştırın: ./install.sh"
    exit 1
fi

# Python3 kontrolü
echo "📦 Python3 kontrol ediliyor..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 bulunamadı. Kuruluyor..."
    sudo apt update
    sudo apt install python3 python3-pip -y
else
    echo "✅ Python3 bulundu"
fi

# PyQt5 kontrolü ve kurulumu
echo ""
echo "📦 PyQt5 kontrol ediliyor..."
if ! python3 -c "import PyQt5" &> /dev/null; then
    echo "❌ PyQt5 bulunamadı. Kuruluyor..."
    sudo apt install python3-pyqt5 -y
    pip3 install PyQt5 --break-system-packages 2>/dev/null
else
    echo "✅ PyQt5 bulundu"
fi

# psutil kontrolü ve kurulumu
echo ""
echo "📦 psutil kontrol ediliyor..."
if ! python3 -c "import psutil" &> /dev/null; then
    echo "❌ psutil bulunamadı. Kuruluyor..."
    pip3 install psutil --break-system-packages
else
    echo "✅ psutil bulundu"
fi

# Dosya izinlerini ayarla
echo ""
echo "🔧 Dosya izinleri ayarlanıyor..."
chmod +x system_monitor.py

# Autostart dizini oluştur
echo ""
echo "🔧 Autostart yapılandırması..."
mkdir -p ~/.config/autostart

# Desktop entry oluştur
CURRENT_DIR=$(pwd)
cat > ~/.config/autostart/system-monitor.desktop << EOF
[Desktop Entry]
Type=Application
Name=System Performance Monitor
Comment=Kali Linux Sistem Performans Monitörü
Exec=python3 $CURRENT_DIR/system_monitor.py
Icon=utilities-system-monitor
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "✅ Autostart yapılandırıldı"

# Test çalıştırması
echo ""
echo "🧪 Kurulum testi yapılıyor..."
if python3 -c "import sys; from PyQt5.QtWidgets import QApplication; import psutil" 2>/dev/null; then
    echo "✅ Tüm bağımlılıklar başarıyla yüklendi!"
else
    echo "⚠️  Bazı bağımlılıklar eksik olabilir"
    exit 1
fi

echo ""
echo "================================"
echo "✅ Kurulum Tamamlandı!"
echo "================================"
echo ""
echo "Kullanım:"
echo "  Başlatmak için: python3 system_monitor.py"
echo "  Arka planda: nohup python3 system_monitor.py &"
echo "  Otomatik başlatma: Sistem yeniden başladığında otomatik çalışacak"
echo ""
echo "Şimdi programı başlatmak ister misiniz? (e/h)"
read -r answer

if [ "$answer" = "e" ] || [ "$answer" = "E" ]; then
    echo "🚀 Program başlatılıyor..."
    python3 system_monitor.py &
    echo "✅ Program başlatıldı!"
    echo "💡 System tray'de simgeyi görebilirsiniz"
else
    echo "Manuel başlatmak için: python3 system_monitor.py"
fi

echo ""
echo "📚 Daha fazla bilgi için README.md dosyasını okuyun"
