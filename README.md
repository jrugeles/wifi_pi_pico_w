# wifi_pi_pico_w
Medición de RSSI usando UDP

# Raspberry Pi Pico W – Demo de Medición de RSSI vía UDP

Este repositorio contiene dos scripts en MicroPython para un escenario de medición de RSSI (Received Signal Strength Indicator): Server_UDP.py y UDP_client.py.

### Server_UDP.py

- **Soft-AP Wi-Fi**  
  Configura el Pico W como punto de acceso con SSID `PicoWAP_JJR` y contraseña `12345678`, mostrando su IP en consola.

- **Heartbeat LED**  
  Parpadea el LED interno (GPIO 25, alias `LED`) cada 500 ms para indicar que el bucle principal sigue vivo.

- **Socket UDP no bloqueante**  
  Abre un socket UDP en `0.0.0.0:5005` con `setblocking(False)` para poder alternar entre lectura de datagramas y blink sin bloquear.

- **Procesamiento de datagramas**  
  - Lee paquetes de hasta 64 bytes.  
  - Si llegan con formato `"MAC,RSSI"`, extrae y muestra en consola:
    ```
    <IP_cliente> <- <MAC> -> <RSSI> dBm
    ```
  - Si el payload está mal formado, imprime un mensaje de error.

- **Eficiencia de CPU**  
  Tras cada iteración ejecuta `time.sleep_ms(10)` para ceder tiempo al sistema y mantener un parpadeo fluido sin consumir 100 % de la CPU.

### UDP_client.py

### Cliente (Nodo fijo – STA + OLED + UDP Sender)

- **Modo STA Wi-Fi**  
  Conecta el Pico W a la red `PicoWAP_JJR` (contraseña `12345678`) y reconecta automáticamente si se pierde la señal, reiniciándose tras 15 s de fallo.

- **Heartbeat LED**  
  Parpadea el LED interno (GPIO 25, alias `LED`) cada 500 ms tanto durante la conexión inicial como en el bucle principal para indicar que el código sigue activo.

- **OLED SSD1306**  
  Muestra en tiempo real la última medición de RSSI en una pantalla I²C de 128×32 px (GP14=SDA, GP15=SCL), o “no disponible” si falla la lectura.

- **Medición de RSSI**  
  - Intenta `wlan.status("rssi")` para lectura rápida.  
  - Si no está disponible, hace un escaneo (`wlan.scan()`) y filtra por SSID para extraer el valor.

- **Formateo de MAC**  
  Recupera la dirección MAC del cliente (`wlan.config("mac")`) y la envía junto al RSSI.

- **Envío UDP**  
  Cada `INTERVAL` s (por defecto 0.5 s) envía un datagrama `"<MAC>,<RSSI>"` al servidor UDP en `192.168.4.1:5005`.  
  Captura y maneja cualquier `OSError` para no interrumpir el bucle.

- **Eficiencia de CPU**  
  Usa `time.sleep_ms(...)` tras cada envío para mantener un muestreo constante sin saturar la CPU.




# ¿Por qué UDP y no HTTP/TCP?

En sistemas embebidos como los dispositivos Raspberry pi pico W, UDP puede ser una buena alternativa para realizar mediciones de potencia RSSI. UDP se diferencia de HTTP/TCP por su simplicidad y mínimo overhead: al no requerir el establecimiento de conexión (three-way handshake) ni el empaquetado de cabeceras HTTP, cada datagrama puede transmitirse y procesarse en milisegundos, lo cual es fundamental cuando se quiere muestrear el RSSI a alta frecuencia. 

Aunque UDP no garantiza la entrega ni el orden de los paquetes, en un experimento de medición de potencia de señal donde se requieren obtener muchas muestras, la pérdida ocasional de un datagrama es admisible y compensa ampliamente la agilidad obtenida. En contraste, HTTP/TCP añade retransmisiones automáticas, control de flujo y confirmaciones que, en un microcontrolador como el Pico W, implican latencias de decenas o cientos de milisegundos y consumen más CPU y memoria. 

Para medir el RSSI, el nodo fijo Raspberry Pi Pico W emplea primero el método nativo wlan.status("rssi") —rápido y directo— y, si no está soportado en su versión de firmware, realiza un escaneo (wlan.scan()) filtrando por el SSID del AP, garantizando siempre una lectura válida del nivel de señal recibida.




