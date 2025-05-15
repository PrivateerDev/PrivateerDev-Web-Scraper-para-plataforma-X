# XScraper - Web Scraping para X (Twitter) 

---

```markdown
# 🕷️ PrivateerDev Web Scraper para Plataforma X (antes Twitter)

Un scraper automatizado escrito en **Python + Selenium**, diseñado para recolectar datos públicos de la plataforma **X (antes Twitter)**. Este proyecto permite realizar búsquedas automatizadas y recolectar tweets con información relevante para análisis de datos, estudios de comportamiento en redes sociales y minería de texto.

---

## 📦 Versiones Disponibles

### 🚀 Versión 1.0 — `twitter_scraperV1.0.py`

#### ✔️ Funcionalidades
- Automatiza la navegación por X mediante Selenium.
- Permite búsqueda por hashtags o nombres de usuario.
- Extrae información básica de los tweets:
  - 📝 Contenido
  - ❤️ Likes
  - 🔁 Retweets
  - 💬 Respuestas
  - 📅 Fecha de publicación
- Guarda los resultados en un archivo `.csv`.

#### ⚙️ Tecnologías
- `Python 3.x`
- `Selenium`
- `ChromeDriver` u otro WebDriver compatible

---

### 🧠 Versión 1.1 — `twitter_scraperV1.1.py`

#### 🔧 Mejoras sobre la versión anterior
- **✔️ Refactorización completa:** Código modular y reutilizable.
- **🛡️ Manejo de errores mejorado:** Excepciones específicas, mensajes claros.
- **⚡ Mayor eficiencia:** Sustitución de `sleep()` por `WebDriverWait`.
- **🧽 Limpieza de datos mejorada:** Remoción de caracteres especiales, HTML, etc.
- **🗃️ Guardado dinámico de archivos:** Nombres personalizados, prevención de sobrescritura.
- **💬 Comentarios y documentación mejorados:** Código autoexplicativo.

---

## 🔍 Comparativa de versiones

| Característica                  | `V1.0`                              | `V1.1`                                                  |
|-------------------------------|-------------------------------------|---------------------------------------------------------|
| Estructura del código         | Procedural                          | Modular, funciones separadas                            |
| Manejo de errores             | Básico (`try/except` genérico)     | Avanzado (`try/except` específicos y tolerante a fallos)|
| Esperas y tiempos             | `time.sleep()`                      | `WebDriverWait`                                         |
| Limpieza de texto             | Parcial                             | Completa y optimizada                                   |
| Guardado de archivos CSV      | Estático                            | Dinámico y con validaciones                             |
| Comentarios/documentación     | Escasos                             | Completos y explicativos                                |

---

## 📁 Estructura del Repositorio

```

PrivateerDev-Web-Scraper-para-plataforma-X/
│
├── twitter\_scraperV1.0.py         # Versión inicial del scraper
├── twitter\_scraperV1.1.py         # Versión optimizada y mejorada
├── requirements.txt               # Dependencias del proyecto
└── README.md                      # Este archivo

````

---

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/PrivateerDev/PrivateerDev-Web-Scraper-para-plataforma-X.git

# 2. Entrar al directorio del proyecto
cd PrivateerDev-Web-Scraper-para-plataforma-X

# 3. Instalar dependencias
pip install -r requirements.txt
````

---

## ⚠️ Aviso Legal

Este proyecto fue creado exclusivamente con fines **educativos y de análisis de datos públicos**.
El uso indebido del mismo puede **violar los Términos de Servicio** de la plataforma X (Twitter).
**El autor no se hace responsable** por cualquier mal uso del software.

---

## 📫 Contacto

¿Comentarios o sugerencias? Abre un issue en este repositorio o contáctanos directamente en [https://github.com/PrivateerDev](https://github.com/PrivateerDev).

---

