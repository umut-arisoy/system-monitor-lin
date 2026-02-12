#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manuel CSV Rapor Oluşturucu
Sistem monitörü çalışmıyorken bile rapor almanızı sağlar
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def export_report(hours=24, filename=None):
    """Belirtilen saat aralığı için CSV raporu oluştur"""
    
    db_path = "system_monitor.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Veri çek
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT timestamp, cpu_percent, memory_percent, 
                   network_sent_mbps, network_recv_mbps,
                   disk_read_mbps, disk_write_mbps
            FROM performance_log 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))
        
        data = cursor.fetchall()
        
        if not data:
            print(f"❌ Son {hours} saat için veri bulunamadı!")
            return False
        
        # Dosya adı oluştur
        if filename is None:
            filename = f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # CSV yaz
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('Timestamp,CPU%,RAM%,Net_Send_Mbps,Net_Recv_Mbps,Disk_Read_MBs,Disk_Write_MBs\n')
            for row in data:
                f.write(f"{row[0]},{row[1]:.2f},{row[2]:.2f},{row[3]:.2f},{row[4]:.2f},{row[5]:.2f},{row[6]:.2f}\n")
        
        print(f"✅ Rapor oluşturuldu: {filename}")
        print(f"📊 Toplam {len(data)} kayıt")
        
        # İstatistikler
        cursor.execute('''
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                MIN(cpu_percent) as min_cpu,
                AVG(memory_percent) as avg_mem,
                MAX(memory_percent) as max_mem,
                MIN(memory_percent) as min_mem
            FROM performance_log 
            WHERE timestamp >= ?
        ''', (since,))
        
        stats = cursor.fetchone()
        
        print("\n📈 İstatistikler:")
        print(f"   CPU  - Ort: {stats[0]:.1f}% | Max: {stats[1]:.1f}% | Min: {stats[2]:.1f}%")
        print(f"   RAM  - Ort: {stats[3]:.1f}% | Max: {stats[4]:.1f}% | Min: {stats[5]:.1f}%")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def show_database_info():
    """Veritabanı bilgilerini göster"""
    
    db_path = "system_monitor.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Toplam kayıt sayısı
        cursor.execute('SELECT COUNT(*) FROM performance_log')
        total = cursor.fetchone()[0]
        
        # En eski kayıt
        cursor.execute('SELECT MIN(timestamp) FROM performance_log')
        oldest = cursor.fetchone()[0]
        
        # En yeni kayıt
        cursor.execute('SELECT MAX(timestamp) FROM performance_log')
        newest = cursor.fetchone()[0]
        
        print("\n📊 Veritabanı Bilgileri:")
        print(f"   Toplam Kayıt: {total}")
        print(f"   En Eski Kayıt: {oldest}")
        print(f"   En Yeni Kayıt: {newest}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def main():
    """Ana fonksiyon"""
    
    print("=" * 50)
    print("Sistem Monitörü - Manuel CSV Rapor Oluşturucu")
    print("=" * 50)
    
    # Komut satırı argümanları
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print("❌ Geçersiz saat değeri!")
            print("Kullanım: python3 export_report.py [saat]")
            sys.exit(1)
    else:
        hours = 24
    
    # Veritabanı bilgilerini göster
    show_database_info()
    
    print(f"\n📅 Son {hours} saat için rapor oluşturuluyor...")
    export_report(hours)
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    main()
