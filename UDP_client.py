import network
import socket
import time
import machine
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# --- Parámetros de red ---
SSID = "PicoWAP_JJR"
PASSWORD = "SecurePass123!"  # Contraseña más segura
SERVER_IP = "192.168.4.1"
SERVER = (SERVER_IP, 5005)
INTERVAL = 1.0  # Intervalo aumentado a 1s para menor consumo

# --- Heartbeat LED ---
led = Pin("LED", Pin.OUT)
BLINK_INTERVAL = 500  # ms
_last_blink = time.ticks_ms()

# --- Contador de paquetes ---
packet_count = 0

# --- Inicializar OLED SSD1306 ---
WIDTH, HEIGHT = 128, 32
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

def oled_message(line1, line2=""):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(f"IP: {wlan.ifconfig()[0]}", 0, 10)
    oled.text(f"Pkts: {packet_count}", 0, 20)
    oled.show()

# --- Función para leer RSSI con promediado ---
def read_rssi(samples=3, delay_ms=50):
    rssi_values = []
    if wlan.isconnected() and wlan.config("ssid") == SSID:
        for _ in range(samples):
            try:
                rssi = wlan.status("rssi")
                if rssi is not None and -100 <= rssi <= -20:
                    rssi_values.append(rssi)
            except:
                pass
            time.sleep_ms(delay_ms)
    return sum(rssi_values) // len(rssi_values) if rssi_values else None

# --- Asegurar conexión Wi-Fi ---
def ensure_wifi(max_retries=3, base_delay=2):
    if wlan.isconnected():
        return
    oled_message("Wi-Fi:", "Conectando...")
    for attempt in range(max_retries):
        wlan.connect(SSID, PASSWORD)
        t0 = time.time()
        while not wlan.isconnected() and time.time() - t0 < 10:
            now = time.ticks_ms()
            if time.ticks_diff(now, _last_blink) >= BLINK_INTERVAL:
                led.toggle()
                _last_blink = now
            time.sleep(0.1)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("🔌 Conectado, IP:", ip)
            oled_message("Wi-Fi OK", ip)
            return
        time.sleep(base_delay * (2 ** attempt))  # Backoff exponencial
    print("⚠️ Fallo de conexión persistente")
    oled_message("Wi-Fi:", "Fallo conexión")
    time.sleep(60)  # Espera larga antes de reintentar

# --- 1) Preparar la interfaz STA ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# --- 2) Conectar por primera vez ---
oled_message("Wi-Fi:", "Conectando...")
wlan.connect(SSID, PASSWORD)
t0 = time.time()
while not wlan.isconnected():
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_blink) >= BLINK_INTERVAL:
        led.toggle()
        _last_blink = now
    if time.time() - t0 > 15:
        machine.reset()
    time.sleep(0.1)

ip = wlan.ifconfig()[0]
print("✅ Conectado →", wlan.ifconfig())
oled_message("Conectado a", SSID)

# --- 3) Formatear MAC y preparar socket UDP ---
mac = ":".join("{:02x}".format(b) for b in wlan.config("mac"))
print("MAC del nodo:", mac)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.1)  # Timeout corto para evitar bloqueos

# --- 4) Bucle principal ---
while True:
    # Heartbeat LED
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_blink) >= BLINK_INTERVAL:
        led.toggle()
        _last_blink = now

    # Asegurar conexión
    ensure_wifi()

    # Medir RSSI
    rssi = read_rssi()
    if rssi is None:
        print("⚠️ RSSI no disponible")
        oled_message("RSSI:", "no disponible")
    else:
        msg = f"{mac},{rssi}"
        oled_message(f"RSSI: {rssi} dBm")
        print("→", msg)
        try:
            sock.sendto(msg.encode(), SERVER)
            packet_count += 1
        except OSError as e:
            print("❌ Error UDP:", e)
            try:
                sock.close()
            except:
                pass
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.1)

    # Modo de bajo consumo
    machine.lightsleep(int(INTERVAL * 1000))