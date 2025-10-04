# PharmaDock AI

PharmaDock AI es una plataforma web donde se pueden realizar experimentos de docking molecular a través de consultas de lenguaje natural gracias a la integración de un chatbot usando el modelo gtp-4o de OpenAI.

# Autores

Este proyecto constituye el Trabajo de Fin de Grado de Carolina Rey López para el Grado de Ingeniería Informática de la Universidade da Coruña.

# Manual de instalación

## Requisitos previos

- **Python 3.13** o superior.
- **python3.13-venv** para la gestión de entornos virtuales
- **pip** para la gestión de paquetes.
- **make** en Ubuntu, para facilitar la instalación.

## Instalación

Dentro de la carpeta del proyecto, escribir en terminal:

- **Linux:** `make install`

- **Windows:** Introduce los siguientes comandos:
	`python -m venv .venv`
    `.venv/Scripts/activate`
    `pip install -r requirements.txt` 

## Ejecución de la aplicación

Desde terminal, ejecutamos el comando:

- **Linux:** `make run`
- **Windows:** `.venv\Scripts\activate & python manage.py runserver`

> [!NOTE]
>
> Algunas funcionalidades tales como el envío de correos de verificación o el funcionamiento del chatbot no funcionarán. Para que funcionen correctamente, se debe crear un directorio .config con un fichero config.env donde se indiquen las variables de entorno necesarias. Este debe cubrirse de la siguiente forma:
>
> ```
>	OPENAI_API_KEY=tu_api_KEY
>	EMAIL_HOST=email_host
>	EMAIL_PORT=email_port
>	EMAIL_HOST_USER=email
>	EMAIL_HOST_PASSWORD=contraseña_email
>```
