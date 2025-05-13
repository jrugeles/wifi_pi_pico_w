import network
import socket
import time
import machine
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ——— Parámetros de red ———
SSID       = "PicoWAP_JJR"
PASSWORD   = "12345678"
SERVER_IP  = "192.168.4.1"
SERVER      = (SERVER_IP, 5005)
INTERVAL   = 0.5    # segundos entre mediciones

# ——— Heartbeat LED en GPIO25 ———
led            = Pin("LED", Pin.OUT)
BLINK_INTERVAL = 500   # ms
_last_blink    = time.ticks_ms()

# ——— Inicializar OLED SSD1306 ———
WIDTH, HEIGHT = 128, 32
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

def oled_message(line1, line2=""):
    oled.fill(0)
    oled.text(line1, 0, 0)
    if line2:
        oled.text(line2, 0, 10)
    oled.show()

# ——— 1) Preparar la interfaz STA ———
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def ensure_wifi():
    if not wlan.isconnected():
        oled_message("Wi-Fi:", "Conectando...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.time()
        while not wlan.isconnected():
            # heartbeat durante espera
            now = time.ticks_ms()
            if time.ticks_diff(now, _last_blink) >= BLINK_INTERVAL:
                led.toggle()
                _last_blink = now
            if time.time() - t0 > 15:
                machine.reset()
            time.sleep(0.1)
        ip = wlan.ifconfig()[0]
        print("🔌 Reconectado, IP:", ip)
        oled_message("Wi-Fi OK", ip)

# ——— 2) Conectar por primera vez ———
oled_message("Wi-Fi:", "Conectando…")
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

# ——— 3) Formatear MAC y preparar socket UDP ———
mac = ":".join("{:02x}".format(b) for b in wlan.config("mac"))
print("MAC del nodo:", mac)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def read_rssi():
    try:
        return wlan.status("rssi")
    except:
        for net in wlan.scan():
            ssid, bssid, ch, rssi, auth, hidden = net
            if ssid.decode() == SSID:
                return rssi
    return None

# ——— 4) Bucle principal ———
while True:
    # heartbeat LED
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_blink) >= BLINK_INTERVAL:
        led.toggle()
        _last_blink = now

    # asegurar conexión
    ensure_wifi()

    # medir RSSI
    rssi = read_rssi()
    if rssi is None:
        print("⚠️ RSSI no disponible")
        oled_message("RSSI:", "no disponible")
    else:
        msg = f"{mac},{rssi}"
        # mostrar en pantalla
        oled_message("RSSI dBm:", str(rssi))
        print("→", msg)
        # enviar UDP
        try:
            sock.sendto(msg.encode(), SERVER)
        except OSError as e:
            print("❌ Error UDP:", e)
            try: sock.close()
            except: pass
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    time.sleep_ms(int(INTERVAL * 1000))
