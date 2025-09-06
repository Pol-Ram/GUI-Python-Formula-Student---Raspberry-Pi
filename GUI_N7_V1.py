import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import RPi.GPIO as GPIO
import serial, struct, threading
from PIL import Image
import csv, time   

# ==============================
# CONFIGURACIÓN GPIO
# ==============================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

# ==============================
# CONFIGURACIÓN SERIAL
# ==============================
ser = serial.Serial('/dev/serial0', baudrate=115200, timeout=1)

# ==============================
# VARIABLES DE ARCHIVO CSV
# ==============================
csv_file = None
csv_writer = None

# ==============================
# CONFIGURACIÓN PRINCIPAL TKINTER
# ==============================
root = tk.Tk()
fondo = tk.PhotoImage(file="background.png")
label = tk.Label(root, image=fondo)
label.place(x=0, y=0, relwidth=1, relheight=1)
root.title("Interfaz con STM32")
root.geometry("800x480")
root.resizable(False, False)

background_image = Image.open("car_board_X2.png")
background_image = background_image.resize((800, 480))

# ==============================
# VARIABLES
# ==============================
velocidad_var = tk.DoubleVar()
rpm_var = tk.DoubleVar()
bateria_var = tk.DoubleVar()
temp_var = tk.DoubleVar()
humid_var = tk.DoubleVar()
Ax_var = tk.DoubleVar()
Ay_var = tk.DoubleVar()
Az_var = tk.DoubleVar()
luces_var = tk.BooleanVar()

# ==============================
# FUNCIÓN DE RECEPCIÓN SERIAL
# ==============================
def leer_serial():
    global csv_writer, csv_file
    while True:
        data = ser.read(28)  # 7 floats * 4 bytes
        if len(data) == 28:
            valores = struct.unpack('<7f', data)
            temp_var.set(valores[0])
            humid_var.set(valores[1])
            Ax_var.set(valores[2])
            Ay_var.set(valores[3])
            Az_var.set(valores[4])
            velocidad_var.set(valores[5])
            rpm_var.set(valores[6])

            # Guardar en CSV solo si luces están activas y archivo abierto
            if luces_var.get() and csv_writer is not None:
                csv_writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),  # Marca de tiempo
                    valores[0],  # Temp
                    valores[1],  # Humid
                    valores[2],  # Ax
                    valores[3],  # Ay
                    valores[4],  # Az
                    valores[5],  # Velocidad
                    valores[6],  # RPM
                    bateria_var.get(),  # Batería (slider)
                    "ON"
                ])
                csv_file.flush()  # Guardar en disco inmediatamente

# ==============================
# FUNCIONES DE GUI
# ==============================
def actualizar_valores():
    velocidad_label.config(text=f"{velocidad_var.get():.0f}\nkm/h")
    rpm_label.config(text=f"{rpm_var.get():.0f}\nRPM")
    bateria_label.config(text=f"Battery: {bateria_var.get():.0f}%")
    temp_label.config(text=f"Temp: {temp_var.get():.0f}°C")
    humid_label.config(text=f"Humid: {humid_var.get():.0f}%")
    Ax_label.config(text=f"Ax: {Ax_var.get():.2f}")
    Ay_label.config(text=f"Ay: {Ay_var.get():.2f}")
    Az_label.config(text=f"Az: {Az_var.get():.2f}")
    luces_label.config(text="SAVE: ON" if luces_var.get() else "SAVE: OFF")

# Variable global para almacenar el after
after_id = None

def loop_gui():
    global after_id
    actualizar_valores()
    after_id = root.after(200, loop_gui)

def controlar_luces():
    global csv_file, csv_writer
    if luces_var.get():
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("SAVING ON")
        # Crear nuevo archivo CSV con timestamp
        filename = time.strftime("log_%Y-%m-%d_%H-%M-%S.csv")
        csv_file = open(filename, "w", newline="")
        csv_writer = csv.writer(csv_file)
        # Escribir cabecera
        csv_writer.writerow(["Tiempo", "Temp", "Humid", "Ax", "Ay", "Az", "Velocidad", "RPM", "Bateria", "Luces"])
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        print("SAVING OFF")
        # Cerrar CSV actual si está abierto
        if csv_file is not None:
            csv_file.close()
            csv_file = None
            csv_writer = None
    actualizar_valores()

def on_closing():
    global after_id, csv_file
    if after_id:
        root.after_cancel(after_id)  # Cancelar el after pendiente
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    if csv_file is not None:
        csv_file.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# ==============================
# ETIQUETAS PARA MOSTRAR VALORES
# ==============================
velocidad_label = tk.Label(root, text="0\nkm/h", font=("Digital-7", 45), fg="#00FFFF", bg="black")
velocidad_label.place(x=165, y=170)

rpm_label = tk.Label(root, text="0\nRPM", font=("Digital-7", 45), fg="#00FFFF", bg="black")
rpm_label.place(x=560, y=170)

bateria_label = tk.Label(root, text="Battery: 0%", font=("Digital-7", 14), fg="#00FFFF", bg="black")
bateria_label.place(x=340, y=170)

temp_label = tk.Label(root, text="Temp: 0°C", font=("Digital-7", 14), fg="#00FFFF", bg="black")
temp_label.place(x=340, y=195)

humid_label = tk.Label(root, text="Humid: 0%", font=("Digital-7", 14), fg="#00FFFF", bg="black")
humid_label.place(x=340, y=220)

Ax_label = tk.Label(root, text="Ax: 0", font=("Digital-7", 14), fg="#00FFFF", bg="black")
Ax_label.place(x=340, y=245)

Ay_label = tk.Label(root, text="Ay: 0", font=("Digital-7", 14), fg="#00FFFF", bg="black")
Ay_label.place(x=340, y=270)

Az_label = tk.Label(root, text="Az: 0", font=("Digital-7", 14), fg="#00FFFF", bg="black")
Az_label.place(x=340, y=295)

luces_label = tk.Label(root, text="Save: OFF", font=("Digital-7", 14), fg="#00FFFF", bg="black")
luces_label.place(x=340, y=325)

# ==============================
# SLIDERS
# ==============================
slider_bateria = ttk.Scale(root, from_=0, to=100, orient="horizontal", variable=bateria_var, command=lambda e: actualizar_valores())
slider_bateria.place(x=115, y=400, width=200, height=15)

battery_label = tk.Label(root, text="Battery", font=("Digital-7", 14), fg="#00FFFF", bg="black")
battery_label.place(x=40, y=395)

# ==============================
# SWITCH DE LUCES
# ==============================
check_luces = tk.Checkbutton(root, text="SAVE DATA", variable=luces_var, command=controlar_luces,
                             fg="#00FFFF", bg="black", selectcolor="black", activeforeground="#00FFFF")
check_luces.place(x=550, y=400)

# ==============================
# INICIO DE HILO Y LOOP
# ==============================
hilo_serial = threading.Thread(target=leer_serial, daemon=True)
hilo_serial.start()

loop_gui()
root.mainloop()
