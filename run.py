#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kali Linux Sistem Performans Monitörü
Sürekli çalışan pop-up monitör ve geçmiş rapor özelliği
"""

import sys
import psutil
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QMainWindow, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QComboBox,
                             QMessageBox, QSystemTrayIcon, QMenu)
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QFont, QIcon, QColor

class PerformanceDatabase:
    """Performans verilerini SQLite veritabanında saklar"""
    
    def __init__(self, db_path="system_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanı ve tabloları oluştur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                network_sent_mbps REAL,
                network_recv_mbps REAL,
                disk_read_mbps REAL,
                disk_write_mbps REAL
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_performance(self, cpu, memory, net_sent, net_recv, disk_read, disk_write):
        """Performans verilerini kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO performance_log 
            (cpu_percent, memory_percent, network_sent_mbps, network_recv_mbps, 
             disk_read_mbps, disk_write_mbps)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cpu, memory, net_sent, net_recv, disk_read, disk_write))
        conn.commit()
        conn.close()
    
    def get_history(self, hours=24):
        """Belirli bir süre için geçmiş verileri getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.close()
        return data
    
    def get_statistics(self, hours=24):
        """İstatistiksel özet bilgiler"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                MIN(cpu_percent) as min_cpu,
                AVG(memory_percent) as avg_mem,
                MAX(memory_percent) as max_mem,
                MIN(memory_percent) as min_mem,
                AVG(network_sent_mbps + network_recv_mbps) as avg_net,
                MAX(network_sent_mbps + network_recv_mbps) as max_net
            FROM performance_log 
            WHERE timestamp >= ?
        ''', (since,))
        stats = cursor.fetchone()
        conn.close()
        return stats
    
    def cleanup_old_data(self, days=7):
        """Eski verileri temizle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = datetime.now() - timedelta(days=days)
        cursor.execute('DELETE FROM performance_log WHERE timestamp < ?', (since,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted


class SystemMonitor:
    """Sistem performans verilerini toplar"""
    
    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_time = datetime.now()
    
    def get_metrics(self):
        """Tüm sistem metriklerini al"""
        # CPU kullanımı
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # RAM kullanımı
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Network kullanımı (Mbps)
        current_net_io = psutil.net_io_counters()
        current_time = datetime.now()
        time_delta = (current_time - self.last_time).total_seconds()
        
        if time_delta > 0:
            bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv
            
            net_sent_mbps = (bytes_sent * 8) / (time_delta * 1_000_000)  # Mbps
            net_recv_mbps = (bytes_recv * 8) / (time_delta * 1_000_000)  # Mbps
        else:
            net_sent_mbps = 0
            net_recv_mbps = 0
        
        # Disk I/O (MB/s)
        current_disk_io = psutil.disk_io_counters()
        if time_delta > 0:
            disk_read = current_disk_io.read_bytes - self.last_disk_io.read_bytes
            disk_write = current_disk_io.write_bytes - self.last_disk_io.write_bytes
            
            disk_read_mbps = disk_read / (time_delta * 1_000_000)  # MB/s
            disk_write_mbps = disk_write / (time_delta * 1_000_000)  # MB/s
        else:
            disk_read_mbps = 0
            disk_write_mbps = 0
        
        self.last_net_io = current_net_io
        self.last_disk_io = current_disk_io
        self.last_time = current_time
        
        return {
            'cpu': cpu_percent,
            'memory': memory_percent,
            'net_sent': net_sent_mbps,
            'net_recv': net_recv_mbps,
            'disk_read': disk_read_mbps,
            'disk_write': disk_write_mbps
        }


class MonitorWidget(QWidget):
    """Ekran köşesinde görünen pop-up monitör widget"""
    
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
        self.db = PerformanceDatabase()
        self.init_ui()
        self.init_timer()
        self.dragging = False
        self.offset = QPoint()
        
    def init_ui(self):
        """Arayüzü oluştur"""
        # Pencere özellikleri
        self.setWindowTitle('Sistem Monitörü')
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Başlık
        title = QLabel('📊 Sistem Monitörü')
        title.setFont(QFont('Arial', 10, QFont.Bold))
        title.setStyleSheet("color: #00ff00;")
        layout.addWidget(title)
        
        # CPU Label
        self.cpu_label = QLabel('CPU: --%')
        self.cpu_label.setFont(QFont('Courier', 9))
        layout.addWidget(self.cpu_label)
        
        # RAM Label
        self.ram_label = QLabel('RAM: --%')
        self.ram_label.setFont(QFont('Courier', 9))
        layout.addWidget(self.ram_label)
        
        # Network Label
        self.net_label = QLabel('NET: -- Mbps')
        self.net_label.setFont(QFont('Courier', 9))
        layout.addWidget(self.net_label)
        
        # Disk Label
        self.disk_label = QLabel('DISK: -- MB/s')
        self.disk_label.setFont(QFont('Courier', 9))
        layout.addWidget(self.disk_label)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.history_btn = QPushButton('📈')
        self.history_btn.setToolTip('Geçmiş Rapor')
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedSize(30, 25)
        btn_layout.addWidget(self.history_btn)
        
        self.minimize_btn = QPushButton('_')
        self.minimize_btn.setToolTip('Simge Durumuna Küçült')
        self.minimize_btn.clicked.connect(self.hide)
        self.minimize_btn.setFixedSize(30, 25)
        btn_layout.addWidget(self.minimize_btn)
        
        self.close_btn = QPushButton('✕')
        self.close_btn.setToolTip('Kapat')
        self.close_btn.clicked.connect(self.close_application)
        self.close_btn.setFixedSize(30, 25)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Stil
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
            QLabel {
                border: none;
                padding: 2px;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #00ff00;
                border-radius: 3px;
                color: #00ff00;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        
        # Pencere boyutu ve konumu
        self.setFixedSize(220, 180)
        
        # Ekranın sağ üst köşesine yerleştir
        screen = QApplication.desktop().screenGeometry()
        self.move(screen.width() - self.width() - 20, 50)
    
    def init_timer(self):
        """Güncelleme timer'ını başlat"""
        # Görüntü güncelleme timer'ı (1 saniye)
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)
        
        # Veritabanı kayıt timer'ı (5 saniye)
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.log_to_database)
        self.log_timer.start(5000)
        
        # İlk güncelleme
        self.update_display()
    
    def update_display(self):
        """Görüntüyü güncelle"""
        metrics = self.monitor.get_metrics()
        
        # CPU renklendirme
        cpu_color = self.get_color_for_value(metrics['cpu'])
        self.cpu_label.setText(f"CPU: {metrics['cpu']:.1f}%")
        self.cpu_label.setStyleSheet(f"color: {cpu_color}; border: none;")
        
        # RAM renklendirme
        ram_color = self.get_color_for_value(metrics['memory'])
        self.ram_label.setText(f"RAM: {metrics['memory']:.1f}%")
        self.ram_label.setStyleSheet(f"color: {ram_color}; border: none;")
        
        # Network
        total_net = metrics['net_sent'] + metrics['net_recv']
        self.net_label.setText(f"NET: ↑{metrics['net_sent']:.1f} ↓{metrics['net_recv']:.1f} Mbps")
        self.net_label.setStyleSheet("color: #00aaff; border: none;")
        
        # Disk
        self.disk_label.setText(f"DISK: R{metrics['disk_read']:.1f} W{metrics['disk_write']:.1f} MB/s")
        self.disk_label.setStyleSheet("color: #ffaa00; border: none;")
    
    def get_color_for_value(self, value):
        """Değere göre renk döndür"""
        if value < 50:
            return '#00ff00'  # Yeşil
        elif value < 75:
            return '#ffff00'  # Sarı
        else:
            return '#ff0000'  # Kırmızı
    
    def log_to_database(self):
        """Veritabanına kaydet"""
        metrics = self.monitor.get_metrics()
        self.db.log_performance(
            metrics['cpu'],
            metrics['memory'],
            metrics['net_sent'],
            metrics['net_recv'],
            metrics['disk_read'],
            metrics['disk_write']
        )
    
    def show_history(self):
        """Geçmiş rapor penceresini göster"""
        history_window = HistoryWindow(self.db)
        history_window.exec_()
    
    def close_application(self):
        """Uygulamayı kapat"""
        reply = QMessageBox.question(self, 'Kapat', 
                                     'Sistem monitörünü kapatmak istediğinize emin misiniz?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()
    
    # Pencereyi sürüklemek için
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


class HistoryWindow(QWidget):
    """Geçmiş verileri gösteren pencere"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        """Rapor arayüzünü oluştur"""
        self.setWindowTitle('Performans Geçmişi ve Rapor')
        self.setGeometry(100, 100, 900, 600)
        
        layout = QVBoxLayout()
        
        # Üst kontroller
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel('Zaman Aralığı:'))
        self.time_combo = QComboBox()
        self.time_combo.addItems(['Son 1 Saat', 'Son 6 Saat', 'Son 24 Saat', 
                                  'Son 3 Gün', 'Son 7 Gün'])
        self.time_combo.setCurrentIndex(2)
        self.time_combo.currentIndexChanged.connect(self.load_data)
        control_layout.addWidget(self.time_combo)
        
        self.refresh_btn = QPushButton('🔄 Yenile')
        self.refresh_btn.clicked.connect(self.load_data)
        control_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton('💾 CSV Dışa Aktar')
        self.export_btn.clicked.connect(self.export_to_csv)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # İstatistikler
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont('Arial', 9))
        layout.addWidget(self.stats_label)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['Zaman', 'CPU %', 'RAM %', 
                                              'Net Gönder (Mbps)', 'Net Al (Mbps)',
                                              'Disk Okuma (MB/s)', 'Disk Yazma (MB/s)'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Stil
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #00ff00;
            }
            QTableWidget {
                gridline-color: #2a2a2a;
                background-color: #1a1a1a;
                color: #00ff00;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #00ff00;
                padding: 5px;
                border: 1px solid #1a1a1a;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #00ff00;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #00ff00;
                padding: 3px;
            }
        """)
        
        self.load_data()
    
    def get_hours_from_selection(self):
        """Seçime göre saat sayısını döndür"""
        index = self.time_combo.currentIndex()
        hours_map = {0: 1, 1: 6, 2: 24, 3: 72, 4: 168}
        return hours_map.get(index, 24)
    
    def load_data(self):
        """Verileri yükle"""
        hours = self.get_hours_from_selection()
        data = self.db.get_history(hours)
        stats = self.db.get_statistics(hours)
        
        # İstatistikleri göster
        if stats and stats[0] is not None:
            stats_text = f"""
            <b>İstatistikler ({self.time_combo.currentText()}):</b><br>
            CPU: Ort: {stats[0]:.1f}% | Max: {stats[1]:.1f}% | Min: {stats[2]:.1f}%<br>
            RAM: Ort: {stats[3]:.1f}% | Max: {stats[4]:.1f}% | Min: {stats[5]:.1f}%<br>
            Network: Ort: {stats[6]:.1f} Mbps | Max: {stats[7]:.1f} Mbps
            """
            self.stats_label.setText(stats_text)
        
        # Tabloyu doldur
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row[1]:.1f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row[2]:.1f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row[3]:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row[4]:.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row[5]:.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{row[6]:.2f}"))
    
    def export_to_csv(self):
        """CSV dosyasına aktar"""
        hours = self.get_hours_from_selection()
        data = self.db.get_history(hours)
        
        filename = f"system_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w') as f:
            f.write('Timestamp,CPU%,RAM%,Net_Send_Mbps,Net_Recv_Mbps,Disk_Read_MBs,Disk_Write_MBs\n')
            for row in data:
                f.write(f"{row[0]},{row[1]:.2f},{row[2]:.2f},{row[3]:.2f},{row[4]:.2f},{row[5]:.2f},{row[6]:.2f}\n")
        
        QMessageBox.information(self, 'Başarılı', f'Rapor kaydedildi: {filename}')


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Ana monitör widget
    monitor = MonitorWidget()
    monitor.show()
    
    # System tray icon (isteğe bağlı)
    tray_icon = QSystemTrayIcon(app)
    tray_icon.setToolTip('Sistem Monitörü')
    
    # Tray menü
    tray_menu = QMenu()
    show_action = tray_menu.addAction('Göster')
    show_action.triggered.connect(monitor.show)
    quit_action = tray_menu.addAction('Çıkış')
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(lambda reason: monitor.show() if reason == QSystemTrayIcon.Trigger else None)
    tray_icon.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
