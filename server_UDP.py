import network
import socket
import time
from machine import Pin
import select

# --- Parámetros de red ---
SSID = "PicoWAP_JJR"
PASSWORD = "SecurePass123!"  # Contraseña más segura
PORT = 5005

# --- Heartbeat LED ---
led = Pin("LED", Pin.OUT)
led_state = False
BLINK_MS = 500  # Parpadeo cada 500 ms
last_blink = time.ticks_ms()

# --- Registro de clientes ---
clients = {}  # Diccionario para almacenar clientes: {mac:,
              # ip, rssi, last_seen}

# 1) Levantar Soft-AP
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
time.sleep(1)
print("AP activo →", ap.ifconfig()[0])

# 2) Configurar servidor UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.setblocking(False)
print("UDP listener en 0.0.0.0:{}".format(PORT))

# 3) Bucle principal
while True:
    # a) Blink del LED
    now = time.ticks_ms()
    if time.ticks_diff(now, last_blink) >= BLINK_MS:
        led_state = not led_state
        led.value(led_state)
        last_blink = now

    # b) Leer datagramas UDP con select
    readable, _, _ = select.select([sock], [], [], 0.01)
    if sock in readable:
        try:
            data, addr = sock.recvfrom(64)
            # Validar IP (solo subred 192.168.4.x)
            if addr[0].startswith("192.168.4."):
                try:
                    mac, rssi = data.decode().split(",")
                    clients[mac] = {
                        "ip": addr[0],
                        "rssi": rssi,
                        "last_seen": time.time()
                    }
                    print(f"{addr[0]} <- {mac} -> {rssi} dBm | Clientes: {len(clients)}")
                except Exception as e:
                    print("UDP mal formado:", data, "error:", e)
            else:
                print(f"Ignorando paquete de IP no válida: {addr[0]}")
        except OSError:
            pass

    # c) Limpiar clientes inactivos (timeout de 60 segundos)
    now = time.time()
    clients = {k: v for k, v in clients.items() if now - v["last_seen"] < 60}

    # d) Pequeña pausa para ceder CPU
    time.sleep_ms(10)