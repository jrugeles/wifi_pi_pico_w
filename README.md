# wifi_pi_pico_w
Medición de RSSI usando UDP

## Raspberry Pi Pico W – Demo de Medición de RSSI vía UDP

Este repositorio contiene dos scripts en MicroPython para medir y reportar la intensidad de la señal RSSI (*Received Signal Strength Indicator*) utilizando un sistema cliente-servidor UDP: `server_UDP.py` y `UDP_client.py`. Los scripts están optimizados para Raspberry Pi Pico W, con mejoras en precisión, robustez, eficiencia energética y escalabilidad.

---

### Server_UDP.py

**Descripción:** Configura un Raspberry Pi Pico W como punto de acceso (Soft-AP) y servidor UDP que recibe y procesa datagramas con lecturas de RSSI desde uno o más clientes.

- **Soft-AP Wi-Fi**  
  Crea un punto de acceso con SSID `PicoWAP_JJR` y una contraseña segura (`SecurePass123!`). Muestra la IP asignada (por defecto `192.168.4.1`) en la consola.

- **Heartbeat LED**  
  Parpadea el LED interno (GPIO 25, alias `LED`) cada 500 ms para indicar que el bucle principal está activo.

- **Socket UDP no bloqueante**  
  Abre un socket UDP en `0.0.0.0:5005` utilizando `select` para una gestión eficiente de múltiples clientes sin bloquear el bucle principal.

- **Procesamiento de datagramas**  
  - Lee paquetes de hasta 64 bytes en formato `"MAC,RSSI"`.  
  - Valida que la IP del cliente pertenezca a la subred `192.168.4.x` para mayor seguridad.  
  - Almacena los datos en un diccionario de clientes (`clients`) con la IP, MAC, RSSI y *timestamp* de última recepción.  
  - Muestra en consola:  
    ```
    <IP_cliente> <- <MAC> -> <RSSI> dBm | Clientes: <número>
    ```  
  - Maneja errores de datagramas mal formados, imprimiendo mensajes de depuración.

- **Gestión de clientes**  
  Mantiene un registro de clientes activos basado en su MAC y elimina aquellos inactivos tras 60 segundos sin recibir datos, mejorando la escalabilidad.

- **Eficiencia y seguridad**  
  - Usa `time.sleep_ms(10)` tras cada iteración para ceder CPU y mantener un parpadeo fluido.  
  - Filtra paquetes de IPs no válidas para prevenir procesamientos no deseados.

---

### UDP_client.py

**Descripción:** Configura un Raspberry Pi Pico W como cliente en modo estación (STA) que mide el RSSI, lo muestra en una pantalla OLED, y lo envía al servidor UDP.

- **Modo STA Wi-Fi**  
  Conecta a la red `PicoWAP_JJR` (contraseña `SecurePass123!`). Implementa un mecanismo de reconexión robusto con *backoff* exponencial, evitando reinicios innecesarios tras fallos (espera hasta 60 segundos antes de reintentar tras múltiples intentos fallidos).

- **Heartbeat LED**  
  Parpadea el LED interno (GPIO 25, alias `LED`) cada 500 ms para indicar actividad, tanto en la conexión inicial como en el bucle principal.

- **OLED SSD1306**  
  Muestra en una pantalla I²C de 128×32 px (GP14=SDA, GP15=SCL):  
  - RSSI en dBm o “no disponible” si falla la lectura.  
  - IP asignada al cliente.  
  - Contador de paquetes enviados (`Pkts`) para monitoreo.  

- **Medición de RSSI optimizada**  
  - Toma 3 muestras de `wlan.status("rssi")` con 50 ms de separación y calcula el promedio para reducir ruido.  
  - Filtra valores atípicos (solo acepta RSSI entre -100 y -20 dBm).  
  - Verifica que la conexión sea al SSID correcto (`PicoWAP_JJR`) antes de leer RSSI.  
  - Retorna `None` si no hay datos válidos, mostrando un mensaje en la OLED.

- **Formateo de MAC**  
  Obtiene la dirección MAC del cliente (`wlan.config("mac")`) y la formatea como cadena hexadecimal para incluirla en los datagramas.

- **Envío UDP**  
  Cada 1 segundo (intervalo ajustado para menor consumo), envía un datagrama `"<MAC>,<RSSI>"` al servidor en `192.168.4.1:5005`.  
  - Usa un socket con *timeout* de 0.1 segundos para evitar bloqueos.  
  - Maneja errores `OSError`, cerrando y recreando el socket si es necesario.  
  - Incrementa un contador de paquetes enviados (`packet_count`) para monitoreo.

- **Eficiencia energética**  
  - Utiliza `machine.lightsleep` durante los intervalos entre envíos para reducir el consumo de energía, ideal para aplicaciones con batería.  
  - Intervalo de envío aumentado a 1 segundo para equilibrar frecuencia de muestreo y consumo.

---

## ¿Por qué UDP y no HTTP/TCP?

En sistemas embebidos como el Raspberry Pi Pico W, UDP es ideal para medir RSSI debido a su simplicidad y bajo *overhead*. A diferencia de HTTP/TCP, que requieren un *three-way handshake*, retransmisiones, y cabeceras complejas, UDP permite enviar datagramas en milisegundos con un impacto mínimo en CPU y memoria. Esto es crítico para muestreos frecuentes en microcontroladores con recursos limitados.

Aunque UDP no garantiza entrega ni orden de paquetes, la pérdida ocasional de un datagrama es aceptable en aplicaciones de monitoreo de RSSI, donde la alta frecuencia de muestreo (e.g., cada 1 segundo) compensa cualquier dato perdido. Las mejoras implementadas, como el promediado de RSSI y la gestión robusta de sockets, aseguran datos fiables sin sacrificar eficiencia.

El cliente utiliza `wlan.status("rssi")` para lecturas rápidas y precisas, con un mecanismo de promediado que reduce el ruido de las mediciones. La validación del SSID conectado garantiza que las lecturas correspondan al AP correcto, mientras que el modo de bajo consumo (`lightsleep`) extiende la vida útil en aplicaciones alimentadas por batería.

---

## Requisitos

- **Hardware:**  
  - Servidor: Raspberry Pi Pico W.  
  - Cliente: Raspberry Pi Pico W con pantalla OLED SSD1306 (128×32 px) conectada vía I²C (GP14=SDA, GP15=SCL).  
  - Fuente de alimentación (USB o batería para el cliente).

- **Software:**  
  - MicroPython instalado en ambos Pico W (versión reciente recomendada).  
  - Biblioteca `ssd1306.py` para el cliente (disponible en repositorios de MicroPython).  
  - IDE como Thonny o herramienta como `ampy` para cargar los scripts.

---

## Instrucciones de uso

1. **Cargar los scripts:**  
   - Copia `server_UDP.py` al Pico W que actuará como servidor. Para las pruebas renombrar como `main.py` y alimentar con batería. 
   - Copia `UDP_client.py` y `ssd1306.py` al Pico W que actuará como cliente. En la pantalla OLED apareceran los mensajes de conexión y lecturas.

2. **Ejecutar el servidor:**  
   - Al alimentar con batería, el dispositivo servidor inicia main.py. Verifica en el LCD del cliente que el AP esté activo (`AP activo → 192.168.4.1`).  
   - El LED parpadeará cada 500 ms, y la consola mostrará los datagramas recibidos.

3. **Ejecutar el cliente:**  
   - Inicia `UDP_client.py`. La pantalla OLED mostrará el estado de conexión, RSSI, IP, y contador de paquetes.  
   - El LED parpadeará cada 500 ms, y la consola reportará los envíos UDP.

4. **Monitoreo:**  
   - El servidor mostrará la IP, MAC, RSSI y número de clientes activos.  
   - El cliente mostrará lecturas de RSSI en tiempo real y confirmará envíos exitosos.  
   - Para probar múltiples clientes, ejecuta `UDP_client.py` en varios Pico W conectados al mismo AP.

5. **Depuración:**  
   - Si no se reciben datos, verifica la conexión al SSID `PicoWAP_JJR` y la IP del servidor (`192.168.4.1`).  
   - Usa un *sniffer* Wi-Fi (e.g., Wireshark) para inspeccionar paquetes UDP en el puerto 5005.  
   - Revisa los mensajes de error en la consola para identificar problemas de socket o Wi-Fi.





