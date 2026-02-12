#!/bin/bash
# Sistem Monitörü Kaldırma Scripti

echo "================================"
echo "Sistem Monitörü Kaldırma"
echo "================================"
echo ""

# Çalışan process'i durdur
echo "🛑 Çalışan monitör durdruluyor..."
pkill -f system_monitor.py
sleep 2

# Process hala çalışıyor mu kontrol et
if pgrep -f system_monitor.py > /dev/null; then
    echo "⚠️  Process hala çalışıyor, zorla sonlandırılıyor..."
    pkill -9 -f system_monitor.py
fi

echo "✅ Process durduruldu"

# Autostart'ı kaldır
echo ""
echo "🗑️  Autostart yapılandırması kaldırılıyor..."
if [ -f ~/.config/autostart/system-monitor.desktop ]; then
    rm ~/.config/autostart/system-monitor.desktop
    echo "✅ Autostart kaldırıldı"
else
    echo "ℹ️  Autostart zaten yok"
fi

# Veritabanını silme seçeneği
echo ""
echo "Veritabanını da silmek istiyor musunuz? (Tüm geçmiş veriler silinecek)"
echo "(e/h):"
read -r answer

if [ "$answer" = "e" ] || [ "$answer" = "E" ]; then
    if [ -f system_monitor.db ]; then
        rm system_monitor.db
        echo "✅ Veritabanı silindi"
    else
        echo "ℹ️  Veritabanı bulunamadı"
    fi
else
    echo "ℹ️  Veritabanı korundu"
fi

# CSV raporlarını silme seçeneği
echo ""
echo "CSV rapor dosyalarını da silmek istiyor musunuz?"
echo "(e/h):"
read -r answer

if [ "$answer" = "e" ] || [ "$answer" = "E" ]; then
    rm -f system_monitor_report_*.csv 2>/dev/null
    echo "✅ CSV dosyaları silindi"
else
    echo "ℹ️  CSV dosyaları korundu"
fi

echo ""
echo "================================"
echo "✅ Kaldırma Tamamlandı!"
echo "================================"
echo ""
echo "Not: Python paketleri (PyQt5, psutil) kaldırılmadı."
echo "Bunları manuel kaldırmak için:"
echo "  pip3 uninstall PyQt5 psutil -y"
echo ""
echo "Program dosyalarını manuel silmek için:"
echo "  rm system_monitor.py README.md install.sh uninstall.sh"
