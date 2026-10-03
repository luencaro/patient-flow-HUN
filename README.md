# Patient Flow HUN

Proyecto para el **Data Challenge HUN 2026** del Hospital Universidad del Norte y el pregrado de Ciencia de Datos de la Universidad del Norte.

El objetivo es comprender, predecir y optimizar el flujo de pacientes dentro del hospital, identificando cuellos de botella, patrones operacionales y oportunidades de mejora en los tiempos de atención.

## Estructura del proyecto

```
patient-flow-HUN/
├── .gitignore          # archivos que no se suben al repo
├── .gitattributes      # fines de línea entre Linux y Windows
├── .env.example        # plantilla de variables de entorno
├── requirements.txt    # librerías de Python
├── README.md
├── sql/                # consultas SQL
├── src/                # código Python reutilizable
├── data/               # datos locales (no se suben al repo)
│   ├── raw/            # datos crudos, tal como se extraen
│   ├── interim/        # datos a medio procesar
│   └── processed/      # datos finales, listos para análisis
├── dashboard/          # aplicación en Dash
├── docs/               # documentación
└── reports/figures/    # gráficos
```

## Requisitos

- Python 3.14
- Git
- Acceso a la VPN del hospital
- Credenciales de la base de datos

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/USUARIO/patient-flow-HUN.git
cd patient-flow-HUN
```

### 2. Crear y activar el entorno virtual

**Linux:**

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar las librerías

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Copia la plantilla y completa tus credenciales:

```bash
cp .env.example .env          # Linux
copy .env.example .env        # Windows
```

## Agregar una librería nueva

Instálala con el entorno activo y actualiza `requirements.txt`:

```bash
pip install nombre-libreria
pip freeze > requirements.txt
```

## Equipo

- Juan Aguirre
- Luis Cabarcas
- Santiago Pastrana