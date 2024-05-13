import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import re
import math
import threading
import time
import pyaudio
from scipy.stats import binom
import wave
import speech_recognition as sr
import mysql.connector

# Configuración de la conexión a la base de datos
#config = {
#    'user': 'root',
#    'password': '',
#    'host': 'localhost',
#    'database': 'usuario',

hostname='localhost'
username='fernanda'
password='12345'
database='usuario'

def doQuery(con):
    cur= conn.cursor()
    cur.execute('SELECT....')
    for firstname, lastname in cur.fetchall():
        print (firstname, lastname)
    


try:
    # Conectar a la base de datos
    cnx = mysql.connector.connect(host=hostname, user=username,passwd=password,db=database)
    
    # Realizar operaciones con la base de datos
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM usuario")
    
    # Procesar los resultados
    for row in cursor:
        print(row)
    
    # Cerrar la conexión
    cnx.close()

except mysql.connector.Error as err:
    if err.errno == 1045:
        print("Error de autenticación: Verifique las credenciales del usuario 'pma'.")
    else:
        print(f"Error al conectar a la base de datos: {err}")

# Colores
fondo_entrar = "#02507F"
fondo_salir = "#02507F"
fondo_correcto = "#0B90D8"
fondo_incorrecto = "#F40808"
fondo_entrada = "#312FBE"
fondo = "#02507F"
fondo_ventana = "#012F4B"


class Transcribir:
    def __init__(self, formato: pyaudio, canales: int, tasa_muestreo: int, tamanio_bufer: int, ruta_archivo: str):
        self.formato = formato
        self.canales = canales
        self.tasa_muestreo = tasa_muestreo
        self.tamanio_bufer = tamanio_bufer
        self.ruta_archivo = ruta_archivo
        self.audio = None
        self.stream = None
        self.frames = []

    def start_recording(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.formato,
            channels=self.canales,
            rate=self.tasa_muestreo,
            input=True,
            frames_per_buffer=self.tamanio_bufer
        )
        self.stream.start_stream()
        print("Grabación iniciada...")

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            print("Grabación detenida.")

    def record_frames(self):
        while self.stream.is_active():
            data = self.stream.read(self.tamanio_bufer)
            self.frames.append(data)

    def save_audio(self):
        wf = wave.open(self.ruta_archivo, "wb")
        wf.setnchannels(self.canales)
        wf.setsampwidth(self.audio.get_sample_size(self.formato))
        wf.setframerate(self.tasa_muestreo)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        print("Grabación guardada.")

    def transcribe_audio(self):
        try:
            r = sr.Recognizer()
            audio_file = sr.AudioFile(self.ruta_archivo)

            with audio_file as source:
                audio = r.record(source)
            texto = r.recognize_google(audio, language="es-ES")  # Cambiar a es-ES si estás en España

            return texto

        except sr.UnknownValueError:
            print("No se pudo reconocer el audio.")
            return "No se pudo reconocer el audio."
        except sr.RequestError as e:
            print(f"Error en la solicitud: {e}")
            return f"Error en la solicitud: {e}"
        except Exception as exception:
            print(f"Ha ocurrido un error al transcribir el audio: {exception}")
            return f"Ha ocurrido un error al transcribir el audio: {exception}"


def count_words(text):
    # Limpiar el texto y convertirlo en una lista de palabras
    words = re.findall(r'\w+', text.lower())

    # Contar la frecuencia de cada palabra
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    return word_freq


def analyze_text(text):
    word_freq = count_words(text)
    repeated_words = {word: freq for word, freq in word_freq.items() if freq > 1}

    # Calcular el número total de palabras
    total_words = sum(word_freq.values())

    if not repeated_words:
        # Si no hay palabras repetidas, la confianza es del 100%
        confidence_interval = 100
    else:
        # Calcular el número de palabras repetidas
        num_repeated_words = sum(repeated_words.values())

        # Calcular la probabilidad de que haya al menos una palabra repetida
        p = 1 - binom.pmf(0, total_words, 1 / total_words)

        # Calcular el intervalo de confianza utilizando la distribución binomial
        confidence_interval = 100 * (1 - binom.cdf(num_repeated_words - 1, total_words, p))

    return repeated_words, confidence_interval

def regresar():
    ventana_paste.destroy()  # Cerrar la ventana de error

def pegar_texto():
    global texto_paste
    global ventana_paste
    global resultado_text

    # Crear una ventana para pegar el texto
    ventana_paste = tk.Toplevel()
    ventana_paste.title("Pegar Texto")
    ventana_paste.geometry("500x400")
    ventana_paste.resizable(width=False, height=False)
    img = tk.PhotoImage(file="V.png")
    lbl_img = tk.Label(ventana_paste, image=img).place(x=0, y=0, relwidth=1, relheight=1)

    # Área de texto para pegar el texto
    texto_paste = scrolledtext.ScrolledText(ventana_paste, width=40, height=20, wrap=tk.WORD, fg="white",
                                            cursor="hand2", relief="flat", bg=fondo)
    texto_paste.pack(pady=10)
    #texto_paste.place(x=30,y=20)

    # Mostrar el texto del resultado_text en la ventana de pegado
    if resultado_text.get("1.0", tk.END).strip():
        texto_paste.insert(tk.END, resultado_text.get("1.0", tk.END).strip())

    # Botón para analizar el texto pegado
    btn_analizar = tk.Button(ventana_paste, text="Analizar Texto", command=analizar_texto_pegado, fg="white",
                             cursor="hand2", relief="flat", bg=fondo_correcto, font=("Comic Snas Ms", 8, "bold"))
    btn_analizar.pack()
    btn_analizar.place(x=207, y=357)

    # Botón "Regresar"
    boton_regresar = tk.Button(ventana_paste, text="Regresar", command=regresar, fg="white",
    cursor="hand2", relief="flat", bg=fondo_correcto,
    font=("Comic Snas Ms", 8, "bold"))
    boton_regresar.pack()
    boton_regresar.place(x=207, y=400)

    ventana_paste.mainloop()


def analizar_texto_pegado():
    global texto_paste
    global ventana_paste

    # Obtener el texto pegado
    texto = texto_paste.get("1.0", tk.END).strip()

    # Verificar si el texto está vacío
    if texto:
        # Analizar el texto
        repeated_words, confidence_interval = analyze_text(texto)

        # Mostrar resultados en una ventana emergente
        if not repeated_words:
            messagebox.showinfo("Resultados del Análisis", f"No hay palabras repetidas. Confianza: {confidence_interval}%")
        else:
            messagebox.showinfo("Resultados del Análisis", f"Palabras repetidas:\n{repeated_words}\n\nNivel de confianza para el número de palabras repetidas:\n{confidence_interval}%")
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingresa algún texto.")

    # Cerrar la ventana de pegado de texto
    ventana_paste.destroy()


def iniciar_grabacion():
    global transcribir
    global resultado_text
    global volver_grabar_button
    global iniciar_detener_button
    global Guardar_button
    global timer_label

    formato = pyaudio.paInt16
    canales = 2
    tasa_muestreo = 44100
    tamanio_bufer = 1024
    ruta_archivo = "audio_proyecto.wav"

    transcribir = Transcribir(formato, canales, tasa_muestreo, tamanio_bufer, ruta_archivo)

    transcribir.start_recording()

    iniciar_detener_button.config(text="Detener Grabación", command=detener_grabacion)
    Guardar_button.config(state=tk.DISABLED)
    timer_label.config(text="Duración de la grabación: 0 segundos")

    # Crear un hilo para la grabación y el temporizador
    threading.Thread(target=grabacion_y_temporizador).start()


def detener_grabacion():
    global transcribir
    global resultado_text
    global volver_grabar_button
    global iniciar_detener_button
    global Guardar_button
    global timer_label

    transcribir.stop_recording()

    iniciar_detener_button.config(text="Iniciar Grabación", command=iniciar_grabacion)
    Guardar_button.config(state=tk.NORMAL)

    # Transcribir el audio después de detener la grabación
    texto_transcrito = transcribir.transcribe_audio()
    resultado_text.delete(1.0, tk.END)  # Limpiar el texto anterior
    resultado_text.insert(tk.END, texto_transcrito)  # Mostrar el texto transcritor en el cuadro de texto

    # Habilitar el botón "Volver a Grabar"
    volver_grabar_button.config(state=tk.NORMAL)


def grabacion_y_temporizador():
    global transcribir
    global timer_label

    start_time = time.time()
    transcribir.frames = []  # Limpiar frames
    transcribir.record_frames()
    transcribir.save_audio()
    elapsed_time = time.time() - start_time

    timer_label.config(text=f"Duración de la grabación: {int(elapsed_time)} segundos")


def volver_grabar():
    global resultado_text
    global volver_grabar_button
    global iniciar_detener_button
    global timer_label

    resultado_text.delete(1.0, tk.END)  # Limpiar el texto anterior
    volver_grabar_button.config(state=tk.DISABLED)  # Deshabilitar el botón "Volver a Grabar"
    iniciar_detener_button.config(text="Iniciar Grabación", command=iniciar_grabacion)  # Restaurar comando del botón "Iniciar Grabación"
    timer_label.config(text="Duración de la grabación: 0 segundos")  # Reiniciar el temporizador


def regresar_pagina_principal():
    ventana_error.destroy()  # Cerrar la ventana de error
    ventana_login.deiconify()  # Mostrar la ventana de inicio de sesión


def abrir_ventana_correcta():
    ventana_login.withdraw()  # Ocultar la ventana de inicio de sesión

    # Crear la ventana para la transcripción de audio
    ventana_transcripcion = tk.Toplevel()
    ventana_transcripcion.title("Transcripción de Audio")
    ventana_transcripcion.geometry("600x470")
    ventana_transcripcion.resizable(width=False, height=False)
    img = tk.PhotoImage(file="T.png")   
    lbl_img = tk.Label(ventana_transcripcion, image=img).place(x=0, y=0, relwidth=1, relheight=1)

    # Crear botón "Iniciar/Detener Grabación"
    global iniciar_detener_button
    iniciar_detener_button = tk.Button(ventana_transcripcion, text="Iniciar Grabación", command=iniciar_grabacion,
                                       fg="white", cursor="hand2", relief="flat", bg=fondo_correcto,
                                       font=("Comic Snas Ms", 8, "bold"))
    iniciar_detener_button.pack()
    iniciar_detener_button.place(x=434, y=80)

    # Crear cuadro de texto para mostrar el resultado
    global resultado_text
    resultado_text = tk.Text(ventana_transcripcion, height=20, width=42, fg="white", cursor="hand2", relief="flat",
                             bg=fondo)
    resultado_text.pack()
    resultado_text.place(x=40, y=45)

    # Crear botón "Volver a Grabar"
    global volver_grabar_button
    volver_grabar_button = tk.Button(ventana_transcripcion, text="Volver a Grabar", command=volver_grabar,
                                     state=tk.DISABLED, fg="white", cursor="hand2", relief="flat",
                                     bg=fondo_correcto, font=("Comic Snas Ms", 8, "bold"))
    volver_grabar_button.pack()
    volver_grabar_button.place(x=437, y=150)

    # Crear botón "Guardar"
    global Guardar_button
    Guardar_button = tk.Button(ventana_transcripcion, text="Guardar", command=guardar_transcripcion, state=tk.DISABLED,
                               fg="white", cursor="hand2", relief="flat", bg=fondo_correcto,
                               font=("Comic Snas Ms", 8, "bold"))
    Guardar_button.pack()
    Guardar_button.place(x=455, y=227)

    # Crear etiqueta para mostrar el temporizador
    global timer_label
    timer_label = tk.Label(ventana_transcripcion, text="Duración de la grabación: 0 segundos", fg="white",
                           bg=fondo_ventana)
    timer_label.pack()
    timer_label.place(x=40, y=370)

    # Botón para pegar texto
    btn_valorar = tk.Button(ventana_transcripcion, text="Valorar", command=pegar_texto, fg="white", cursor="hand2",
                            relief="flat", bg=fondo_correcto, font=("Comic Snas Ms", 8, "bold"))
    btn_valorar.pack()
    btn_valorar.place(x=455, y=300)

    ventana_transcripcion.mainloop()


def abrir_ventana_incorrecta():
    # Crear la ventana para el mensaje de error
    global ventana_error
    ventana_error = tk.Toplevel()
    ventana_error.title("Error")
    ventana_error.geometry("500x500")
    ventana_error.resizable(width=False, height=False)
    img = tk.PhotoImage(file="M.png")
    lbl_img = tk.Label(ventana_error, image=img).place(x=0, y=0, relwidth=1, relheight=1)

    # Botón "Regresar"
    boton_regresar = tk.Button(ventana_error, text="Regresar", command=regresar_pagina_principal, fg="white",
    cursor="hand2", relief="flat", bg=fondo_incorrecto,
    font=("Bahnschrift Light", 11, "bold"))
    boton_regresar.pack()
    boton_regresar.place(x=210, y=318)

    ventana_error.mainloop()

def guardar_transcripcion():
    global resultado_text
    texto_transcrito = resultado_text.get("1.0", tk.END).strip()

    if texto_transcrito:
        # Guardar en la base de datos
        try:
            # Conexión a la base de datos MySQL
            conexion = mysql.connector.connect(
                host="localhost",
                user="fernanda",
                password="12345",
                database="usuario"
            )

            # Crear el cursor
            cursor = conexion.cursor()

            # Insertar la transcripción en la base de datos
            cursor.execute("INSERT INTO transcribir (texto) VALUES (%s)", (texto_transcrito,))
            conexion.commit()

            # Cerrar la conexión a la base de datos
            cursor.close()
            conexion.close()

            messagebox.showinfo("Guardado", "La transcripción se ha guardado exitosamente en la base de datos.")
        except mysql.connector.Error as error:
            print(f"Error al conectar a MySQL: {error}")
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")

        # Guardar en el dispositivo
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, "w") as file:
                file.write(texto_transcrito)
            messagebox.showinfo("Guardado", "La transcripción se ha guardado exitosamente en el dispositivo.")
    else:
        messagebox.showwarning("Advertencia", "No hay ninguna transcripción para guardar.")



def iniciar_sesion():
    global usuario_entry
    global contrasena_entry
    usuario = usuario_entry.get()
    contrasena = contrasena_entry.get()
    if usuario == "AFED" and contrasena == "1234":
        abrir_ventana_correcta()
    else:
        abrir_ventana_incorrecta()


# Ventana de inicio de sesión
ventana_login = tk.Tk()
ventana_login.title("Inicio de Sesión")
ventana_login.geometry("500x500")
ventana_login.resizable(width=False, height=False)
img = tk.PhotoImage(file="U.png")
lbl_img = tk.Label(ventana_login, image=img).place(x=0, y=0, relwidth=1, relheight=1)

# Crear entrada para el nombre de usuario
usuario_entry = tk.Entry(ventana_login, fg="white", bg=fondo_entrada, insertbackground="white", cursor="hand2", relief="flat",
                            width=10,font=("Bahnschrift Light", 11))
usuario_entry.pack()
usuario_entry.place(x=148, y=176)

# Crear entrada para la contraseña
contrasena_entry = tk.Entry(ventana_login, show="*", fg="white", bg=fondo_entrada, insertbackground="white",
                            width=10,cursor="hand2", relief="flat",
                            font=("Bahnschrift Light", 11))
contrasena_entry.pack()
contrasena_entry.place(x=148, y=263)

def salir():
    ventana_login.destroy()

# Botón "Iniciar Sesión"
boton_iniciar_sesion = tk.Button(ventana_login, text="Entrar", command=iniciar_sesion, fg="white",
                                width=10,cursor="hand2", relief="flat", bg=fondo_entrar,
                                  font=("Bahnschrift Light",11, "bold"))
boton_iniciar_sesion.pack()
boton_iniciar_sesion.place(x=94, y=362)

boton1=tk.Button(ventana_login, text="Salir", command=salir, fg="white",
                                 width=10, cursor="hand2", relief="flat", bg=fondo_salir,
                                  font=("Bahnschrift Light",11, "bold"))
boton1.pack()
boton1.place(x=302,y=362)

ventana_login.mainloop()
