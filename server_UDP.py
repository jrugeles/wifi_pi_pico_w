import network
import socket
import time
from machine import Pin

# — Parámetros de red —
SSID           = "PicoWAP_JJR"
PASSWORD       = "12345678"
PORT           = 5005

# — Heartbeat LED —  
# En Pico W la salida interna está en GP25 y acepta el alias "LED"
led       = Pin("LED", Pin.OUT)  
led_state = False
BLINK_MS  = 500             # Parpadeo cada 500 ms
last_blink = time.ticks_ms()

# 1) Levantar Soft-AP
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
time.sleep(1)
print("AP activo →", ap.ifconfig()[0])

# 2) Configurar servidor UDP no bloqueante
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
        if led_state:
            led.on()
        else:
            led.off()
        last_blink = now

    # b) Leer datagrama UDP (si hay)
    try:
        data, addr = sock.recvfrom(64)
    except OSError:
        # no hay nada que leer
        pass
    else:
        # procesar payload
        try:
            mac, rssi = data.decode().split(",")
            print("{} <- {} -> {} dBm".format(addr[0], mac, rssi))
        except Exception as e:
            print("UDP mal formado:", data, "error:", e)

    # c) Pequeña pausa para ceder CPU
    time.sleep_ms(10)

