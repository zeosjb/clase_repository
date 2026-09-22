# Guía del estudiante: tu primera API por capas

En este proyecto vas a aprender cómo una API recibe una petición, consulta una base de datos y devuelve una respuesta en formato JSON.

Usaremos cuatro tecnologías:

- **Python** como lenguaje;
- **FastAPI** para crear los endpoints;
- **SQLAlchemy** para comunicarnos con la base de datos;
- **SQLite** como base de datos local.

No necesitas entender todo de inmediato. Primero ejecutaremos el proyecto y después seguiremos el recorrido de una petición paso a paso.

## 1. ¿Qué hace esta aplicación?

La aplicación administra usuarios y actualmente permite:

| Método | Ruta | Resultado |
|---|---|---|
| `GET` | `/` | Comprueba que la API funciona |
| `GET` | `/users/` | Devuelve todos los usuarios |
| `GET` | `/users/{user_id}` | Busca un usuario por su ID |

Por ejemplo, al solicitar `GET /users/1`, podrías recibir:

```json
{
  "id": 1,
  "name": "Ana Torres",
  "email": "ana@example.com"
}
```

Observa que la respuesta no contiene la contraseña. Más adelante veremos por qué.

## 2. Antes de comenzar

Debes tener Python instalado. Puedes comprobarlo desde PowerShell:

```powershell
python --version
```

Ahora abre PowerShell en la carpeta `backend` y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Estos comandos realizan tres acciones:

1. crean un entorno virtual llamado `.venv`;
2. activan ese entorno;
3. instalan las bibliotecas del archivo `requirements.txt`.

El entorno virtual mantiene las dependencias de este proyecto separadas de las de otros proyectos.

## 3. Ejecutar la API

Con el entorno virtual activado, ejecuta:

```powershell
python -m uvicorn app.main:app --reload
```

Deberías ver un mensaje parecido a este:

```text
Uvicorn running on http://127.0.0.1:8000
```

Abre estas direcciones en el navegador:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

La segunda dirección abre **Swagger UI**, una interfaz creada automáticamente por FastAPI. Desde allí puedes probar los endpoints sin instalar otra herramienta.

El parámetro `--reload` reinicia el servidor cuando modificas el código. Se utiliza durante el desarrollo, no en producción.

## 4. El mapa del proyecto

```text
backend/
|-- app/
|   |-- database.py
|   |-- main.py
|   |-- models/
|   |   `-- user.py
|   |-- schemas/
|   |   `-- user.py
|   |-- repositories/
|   |   `-- user_repository.py
|   |-- services/
|   |   `-- user_service.py
|   `-- routers/
|       `-- users.py
|-- GUIA_CLASE.md
`-- requirements.txt
```

El código está separado por responsabilidades. Puedes imaginarlo como un restaurante:

| Parte del proyecto | Comparación | Responsabilidad |
|---|---|---|
| Router | Mesero | Recibe la solicitud del cliente y entrega la respuesta |
| Service | Cocina | Decide cómo debe resolverse la solicitud |
| Repository | Encargado de bodega | Busca o guarda la información |
| Model | Inventario | Describe cómo se almacenan los datos |
| Schema | Formato del plato | Define qué datos pueden entrar o salir |
| Database | Acceso a la bodega | Administra la conexión con la base de datos |
| Main | Apertura del restaurante | Inicia y reúne toda la aplicación |

La comparación no es perfecta, pero ayuda a recordar que cada parte tiene una función distinta.

## 5. `database.py`: conectar la aplicación

El archivo `app/database.py` prepara la comunicación con SQLite.

### 5.1 Dirección de la base de datos

```python
DATABASE_URL = "sqlite:///./database.db"
```

Esta dirección indica que usaremos SQLite y que los datos se guardarán en el archivo `database.db`.

Cuando ejecutes la aplicación por primera vez, ese archivo aparecerá automáticamente en la carpeta desde la que iniciaste Uvicorn.

### 5.2 Motor de SQLAlchemy

```python
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
```

El `engine` es el objeto que administra las conexiones con la base de datos.

La opción `check_same_thread=False` es necesaria en este ejemplo porque FastAPI puede trabajar con varios hilos y SQLite normalmente restringe una conexión al hilo que la creó. Esta opción es específica de SQLite; no debes copiarla automáticamente al usar PostgreSQL o MySQL.

### 5.3 Fábrica de sesiones

```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
```

Una sesión representa el trabajo que hacemos con la base de datos: consultar, agregar, actualizar o eliminar información.

`SessionLocal` no es una sesión abierta. Es una **fábrica** que permite crear sesiones cuando sean necesarias.

### 5.4 Clase base

```python
class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos."""
```

Cada modelo que hereda de `Base` queda registrado por SQLAlchemy. Así puede relacionar una clase de Python con una tabla de la base de datos.

### 5.5 Una sesión por petición

```python
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
```

Este código sigue el siguiente ciclo:

1. `SessionLocal()` abre una sesión;
2. `yield db` entrega la sesión al endpoint;
3. se procesa la petición;
4. `finally` cierra la sesión, incluso si ocurre un error.

Cerrar siempre las sesiones evita dejar conexiones abiertas innecesariamente.

## 6. `models/user.py`: representar la tabla

El modelo `User` representa la tabla `users`:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
```

La relación puede visualizarse así:

| Python | Base de datos |
|---|---|
| Clase `User` | Tabla `users` |
| Atributo `id` | Columna `id` |
| Atributo `name` | Columna `name` |
| Atributo `email` | Columna `email` |
| Atributo `password_hash` | Columna `password_hash` |

Detalles importantes:

- `primary_key=True` convierte `id` en la clave primaria;
- `index=True` ayuda a buscar por `id`;
- `unique=True` impide repetir el mismo correo;
- `password_hash` debe almacenar un hash, nunca la contraseña original.

Un **modelo ORM** explica cómo se almacenan los datos. No define necesariamente todo lo que verá el cliente de la API.

## 7. `schemas/user.py`: controlar entradas y salidas

Los esquemas de Pydantic definen la forma de los datos que recibe o devuelve la API.

### Datos para crear un usuario

```python
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
```

Este esquema representa los datos que un cliente enviaría para crear un usuario. Está preparado para una futura ruta `POST`.

### Datos que puede devolver la API

```python
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
```

`UserResponse` no contiene `password` ni `password_hash`. Por eso FastAPI no incluye esa información en el JSON de respuesta.

Esta separación es importante: la tabla puede contener información interna que nunca debe exponerse públicamente.

```python
model_config = ConfigDict(from_attributes=True)
```

`from_attributes=True` permite que Pydantic cree una respuesta leyendo los atributos de un objeto SQLAlchemy.

## 8. `repositories/user_repository.py`: consultar los datos

El repositorio concentra las operaciones de base de datos:

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(User).all()

    def get_by_id(self, user_id: int):
        return self.db.get(User, user_id)
```

`get_all()` devuelve todos los registros de la tabla `users`.

`get_by_id()` busca un registro utilizando su clave primaria. Si no lo encuentra, devuelve `None`.

El repositorio no decide qué código HTTP utilizar. Su responsabilidad es comunicarse con la base de datos.

## 9. `services/user_service.py`: aplicar las reglas

El servicio utiliza el repositorio y aplica las reglas de la aplicación:

```python
def get_by_id(self, user_id: int):
    user = self.repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    return user
```

La regla es sencilla:

- si el usuario existe, se devuelve;
- si no existe, se genera un error `404 Not Found`.

La consulta pertenece al repositorio. La decisión sobre qué hacer con el resultado pertenece al servicio.

## 10. `routers/users.py`: definir las rutas

El router agrupa las rutas de usuarios:

```python
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)
```

El prefijo `/users` se agrega delante de todas las rutas del archivo.

La función `get_service` construye las dependencias necesarias:

```python
def get_service(db: Session = Depends(get_db)):
    repository = UserRepository(db)
    return UserService(repository)
```

Aquí ocurre lo siguiente:

1. FastAPI ejecuta `get_db` y obtiene una sesión;
2. la sesión se entrega a `UserRepository`;
3. el repositorio se entrega a `UserService`;
4. el servicio se entrega al endpoint.

Este mecanismo se llama **inyección de dependencias**.

El endpoint para buscar un usuario es:

```python
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: UserService = Depends(get_service),
):
    return service.get_by_id(user_id)
```

FastAPI convierte el fragmento de la URL en un número entero y valida la respuesta usando `UserResponse`.

## 11. `main.py`: unir todas las piezas

`main.py` es el punto de entrada de la aplicación.

### Crear las tablas al iniciar

```python
@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
```

Antes de aceptar peticiones, SQLAlchemy crea las tablas que todavía no existan.

`create_all()` es adecuado para este proyecto educativo, pero tiene una limitación: no modifica una tabla existente cuando cambia su modelo. Los proyectos reales suelen utilizar migraciones con una herramienta como Alembic.

### Crear la aplicación

```python
app = FastAPI(
    title="API de Usuarios",
    description="Ejemplo de arquitectura por capas con FastAPI y SQLAlchemy.",
    version="1.0.0",
    lifespan=lifespan,
)
```

Esta es la variable final de `app.main:app`:

```text
app.main:app
 |    |    |
 |    |    `-- variable FastAPI
 |    `------- archivo main.py
 `------------ carpeta app
```

Finalmente, el router se agrega a la aplicación:

```python
app.include_router(users_router)
```

Si no ejecutáramos esa línea, FastAPI no conocería las rutas `/users/`.

## 12. Recorrido completo de una petición

Supongamos que el navegador solicita:

```http
GET /users/1
```

El recorrido completo es:

```text
1. Cliente solicita GET /users/1
              |
2. Router reconoce la ruta y obtiene user_id = 1
              |
3. get_db abre una Session
              |
4. get_service crea Repository y Service
              |
5. Service pide el usuario al Repository
              |
6. Repository consulta la tabla users
              |
7. Service devuelve el usuario o genera un error 404
              |
8. UserResponse selecciona id, name y email
              |
9. FastAPI envía el JSON al cliente
              |
10. get_db cierra la Session
```

Esta separación parece más larga que escribir todo dentro del endpoint, pero facilita probar, mantener y ampliar el proyecto.

## 13. Probar la API paso a paso

### Prueba 1: endpoint principal

Visita `http://127.0.0.1:8000/`.

Resultado esperado:

```json
{
  "message": "API de Usuarios funcionando",
  "documentation": "/docs"
}
```

### Prueba 2: tabla vacía

En Swagger UI, ejecuta `GET /users/`.

Si todavía no agregaste usuarios, recibirás:

```json
[]
```

Una lista vacía no es un error. Significa que la consulta funcionó, pero no encontró registros.

### Prueba 3: usuario inexistente

Ejecuta `GET /users/1`.

Si el usuario no existe, recibirás el código `404` y:

```json
{
  "detail": "Usuario no encontrado"
}
```

## 14. Insertar un usuario de demostración

La API todavía no tiene una ruta `POST`. Para poder probar las consultas, insertaremos temporalmente un usuario desde Python.

Detén Uvicorn con `Ctrl+C` y ejecuta:

```powershell
python
```

Después escribe:

```python
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()

user = User(
    name="Ana Torres",
    email="ana@example.com",
    password_hash="hash_solo_para_la_demostracion",
)

db.add(user)
db.commit()
db.refresh(user)

print(user.id)

db.close()
exit()
```

¿Qué hizo cada operación?

- `add()` preparó el objeto para insertarlo;
- `commit()` confirmó el cambio en la base de datos;
- `refresh()` volvió a leer el objeto para obtener valores generados, como el ID;
- `close()` cerró la sesión.

El texto usado en `password_hash` es solamente demostrativo. Una aplicación real debe generar un hash seguro a partir de la contraseña.

Inicia nuevamente Uvicorn y repite las pruebas. Ahora `GET /users/` debería devolver una lista con Ana y `GET /users/1` debería encontrarla.

## 15. Diferencias que debes recordar

### Modelo frente a esquema

| Modelo SQLAlchemy | Esquema Pydantic |
|---|---|
| Representa una tabla | Representa datos de entrada o salida |
| Se comunica con la base de datos | Valida y transforma datos |
| Puede contener `password_hash` | Puede ocultar `password_hash` |

### Repository frente a service

| Repository | Service |
|---|---|
| Ejecuta consultas | Aplica reglas de negocio |
| Devuelve un usuario o `None` | Convierte `None` en un error 404 |
| Conoce SQLAlchemy | Coordina el caso de uso |

### `engine` frente a `Session`

| Engine | Session |
|---|---|
| Administra conexiones | Representa una unidad de trabajo |
| Se crea una vez | Se crea para cada petición |
| Vive mientras funciona la aplicación | Se cierra después de utilizarse |

## 16. Errores frecuentes

### `ModuleNotFoundError`

Comprueba que activaste `.venv` y que instalaste las dependencias:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Uvicorn no encuentra `app.main`

Ejecuta el comando desde la carpeta `backend`, no desde el interior de `app`:

```powershell
python -m uvicorn app.main:app --reload
```

### El puerto 8000 está ocupado

Utiliza otro puerto:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### Agregué un campo al modelo y la tabla no cambió

`create_all()` crea tablas nuevas, pero no modifica tablas existentes. Durante una práctica sin datos importantes puedes detener la API y eliminar `database.db` para recrearlo. En un proyecto real se utilizan migraciones.

## 17. Comprueba lo que aprendiste

Intenta responder sin mirar las secciones anteriores:

1. ¿Qué objeto administra las conexiones con SQLite?
2. ¿Por qué no usamos una única sesión global?
3. ¿Qué garantiza el bloque `finally` de `get_db`?
4. ¿Cuál es la diferencia entre `User` y `UserResponse`?
5. ¿Por qué `password_hash` no aparece en el JSON?
6. ¿Qué capa ejecuta la consulta a SQLAlchemy?
7. ¿Qué capa transforma un resultado inexistente en un error 404?
8. ¿Para qué sirve `app.include_router(users_router)`?

## 18. Desafíos para continuar

Realiza los desafíos en este orden:

1. Agrega un segundo usuario desde el intérprete de Python.
2. Añade una ruta `POST /users/` utilizando `UserCreate`.
3. Evita que puedan registrarse dos usuarios con el mismo correo.
4. Valida el correo con `EmailStr` de Pydantic.
5. Implementa `DELETE /users/{user_id}`.
6. Agrega una biblioteca para generar hashes seguros.
7. Incorpora Alembic para administrar cambios en las tablas.

## 19. Resumen final

Cuando llega una petición, el router la recibe, el service aplica las reglas y el repository consulta la base de datos. SQLAlchemy transforma registros en objetos de Python y Pydantic convierte esos objetos en respuestas seguras.

La idea central del proyecto no es solamente aprender a consultar SQLite. También es entender que separar responsabilidades hace que una aplicación sea más sencilla de mantener, probar y ampliar.
