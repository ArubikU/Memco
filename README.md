# MemCore

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

Un sistema completo de gestión de memoria con capacidades de búsqueda vectorial, diseñado para el almacenamiento, recuperación y gestión eficientes de información.

## 🚀 Características

- **Sistema de Memoria Completo**: Operaciones CRUD completas para registros de memoria
- **Búsqueda Vectorial**: Búsqueda de similitud semántica mediante embeddings
- **MemQL**: Lenguaje de consulta específico para recuperación de memoria estructurada
- **Almacenamiento Seguro**: Cifrado incorporado para contenido confidencial
- **API Versátil**: Acceso programático a través de CLI y API REST
- **Bibliotecas Cliente**: Integración simplificada con aplicaciones

## 📋 Requisitos

- Python 3.7+
- Dependencias listadas en `setup.py`

## 🔧 Instalación

### Desde PyPI (próximamente)

```bash
pip install memcore
```

### Desde el Código Fuente

```bash
git clone https://github.com/memco/memcore.git
cd memcore
pip install -e .
```

## 🏁 Primeros Pasos

### Ejemplo Básico

```python
from memcore import MemCore, MemoryBuilder
from memcore.embedding import get_embedding_provider

# Inicializar el proveedor de embeddings
embedding_provider = get_embedding_provider()

# Crear una instancia del sistema de memoria con capacidades de búsqueda vectorial
mem_system = MemCore(
    root_path=".memfolder",
    encryption_key="mi_clave_secreta",
    embedding_provider=embedding_provider
)

# Crear un constructor de memoria con el proveedor de embeddings
builder = MemoryBuilder(embedding_provider)

# Crear un nuevo registro de memoria con generación automática de embeddings
memory = builder.set_content("Este es un ejemplo de memoria con embedding vectorial") \
                .set_tags(["ejemplo", "vector", "embedding"]) \
                .set_importance(0.8) \
                .set_source("ejemplo.py") \
                .build()

# Añadir la memoria al sistema
memory_id = mem_system.add_memory(memory, encrypted=True)
print(f"Memoria creada con ID: {memory_id}")

# Recuperar la memoria
retrieved = mem_system.get_memory(memory_id)
print(f"Contenido: {retrieved.content}")
```

### Uso del Cliente

```python
from memcore_client import MemCoreClient

# Inicializar el cliente
client = MemCoreClient("http://localhost:8000")

# Añadir una memoria
memory = client.add_memory(
    content="Esta es una memoria de prueba",
    tags=["prueba", "ejemplo"],
    importance=0.8,
    source="ejemplo.py"
)

# Buscar memorias similares
similar = client.vector_search("memoria de prueba")
print(f"Se encontraron {len(similar)} memorias similares")

# Ejecutar una consulta MemQL
results = client.memql_query("SELECT WHERE tags == \"prueba\" ORDER BY importance DESC")
print(f"La consulta devolvió {len(results)} memorias")
```

## 📚 Arquitectura

MemCore está diseñado como un sistema modular de gestión de memoria con los siguientes componentes clave:

1. **Sistema de Memoria Principal**: Gestiona los registros de memoria y proporciona operaciones CRUD
2. **Búsqueda Vectorial**: Permite la búsqueda de similitud semántica mediante embeddings
3. **MemQL**: Lenguaje de consulta para recuperación estructurada de memoria
4. **Capa de Almacenamiento**: Maneja la persistencia y recuperación de memorias
5. **Capa API**: Proporciona acceso programático a través de CLI y API REST
6. **Bibliotecas Cliente**: Simplifica la integración con aplicaciones

Para más detalles, consulta [ARCHITECTURE.md](ARCHITECTURE.md).

## 🗺️ Hoja de Ruta

Estamos continuamente mejorando MemCore. Estos son nuestros objetivos para las próximas versiones:

### v1.1.0 (Junio 2025)
- **Compresión Avanzada**
- **Sistema de Sincronización**
- **Optimizaciones de Rendimiento**

### v1.2.0 (Julio 2025)
- **Seguridad Mejorada**
- **Características Avanzadas de MemQL**
- **Componentes de UI**

Para más detalles, consulta [ROADMAP.md](ROADMAP.md).

## 👥 Contribuir

¡Las contribuciones son bienvenidas! Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para obtener pautas sobre cómo contribuir al proyecto.

Estamos actualmente enfocados en:
1. Implementación de compresión avanzada
2. Sistema de sincronización
3. Optimizaciones de rendimiento para grandes conjuntos de datos
4. Mejora de la documentación y ejemplos

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2025 MemCore Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
