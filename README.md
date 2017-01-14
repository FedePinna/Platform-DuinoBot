# Platform-DuinoBot
Plataforma de desarrollo Duinobot AVR para Platformio IDE.

Pasos para instalar la Plataforma DuinoBot en PlatformIO IDE

* Instalar Pyhton, descargar la última versión del [Python 2.7.x](https://www.python.org/downloads/) 
* Instalar [PlatformIO IDE](http://platformio.org/platformio-ide)
* Entrar a la terminal desde PlatformIO IDE o desde sistema operativo.
* Instalar la Plataforma de desarrollo DuinoBot.
```bash
  # instalar la ultima versión estable
  >platformio platform install https://github.com/FedePinna/Platform-DuinoBot/archive/v1.0.0.zip

  # instalar la versión de desarrollo
  >platformio platform install https://github.com/FedePinna/Platform-DuinoBot.git
```
* Instalar Clang(Autocompletado de código inteligente), descargar la última versión de [Clang](http://releases.llvm.org/download.html).

Para probar la Plataforma Duinobot descargue el [ejemplo](https://github.com/FedePinna/Platform-DuinoBot/releases/download/v1.0.0/multiplo-blink.zip).
Una vez iniciado PlatformIO IDE ir a:
  * Menu: Platformio > Open Project folder...
  * Seleccionar la carpeta que contiene el proyecto.
  * Compilar y Subir.
  
IMPORTANTE! vx.x.x.zip corresponde a la versión de la platforma, compruebe que instale la [última versión]
(https://github.com/FedePinna/Platform-DuinoBot/releases/latest).
