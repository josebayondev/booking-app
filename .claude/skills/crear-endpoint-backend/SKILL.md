---
name: crear-endpoint-backend
description: Da la forma que debe tener cualquier endpoint nuevo de app/api/ -- una sola función plana, con guard clauses tempranas y comentarios de paso, sin trocear en funciones privadas de un solo uso -- y sirve igual para revisar uno ya escrito. Úsala cuando vayas a escribir un endpoint FastAPI nuevo en app/api/, o cuando te pidan revisar el estilo de uno existente.
---

# Crear (o revisar) un endpoint de `app/api/`

## Regla

Un endpoint es **una sola función**, de arriba a abajo, con sus pasos separados por
comentarios numerados (`# 1. ...`, `# 2. ...`) y guard clauses que cortan pronto con
`raise ApiError(...)`. No se trocea en funciones `_privadas` solo por legibilidad — eso
es justo lo que hace que un fichero con muchos endpoints cueste seguir: cada uno se lee
saltando entre tres o cuatro funciones que solo él llama.

Es una decisión explícita del desarrollador, con un ejemplo real de otro proyecto suyo en
Flask (`validate_pdf_config_sample`): validaciones y guard clauses en línea, con
comentarios marcando cada sección, y solo se delega a otra función lo que es lógica de
negocio genuinamente reutilizable. Con muchos endpoints por delante, quiere ese mismo
patrón aquí — que cada uno se lea de un tirón sin saltar de función en función.

## Cuándo SÍ extraer una función aparte

Solo cuando la lógica se **reutiliza de verdad entre dos o más rutas**. El ejemplo real
del proyecto es `fetch_free_slots` (`app/api/availability.py`): la usan tanto
`GET /availability` como `POST /bookings`, así que vive fuera y las dos la importan. Si
solo la llama un endpoint, se queda dentro de él aunque sean quince líneas.

Lógica de negocio genuinamente compleja (cálculo, no orquestación de una petición HTTP)
sigue yendo a `app/services/` como siempre — eso no cambia, es la otra capa.

## Ejemplo canónico

`app/api/bookings.py` es la referencia viva — léelo entero antes de escribir uno nuevo.
Forma:

```python
@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(
    booking_in: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
) -> Booking:
    # 1. El tipo de cita tiene que existir y estar activo.
    appointment_type = db.scalars(
        select(AppointmentType).where(
            AppointmentType.slug == booking_in.appointment_type,
            AppointmentType.is_active.is_(True),
        )
    ).one_or_none()
    if appointment_type is None:
        raise ApiError(404, "appointment_type_not_found", "No existe ese tipo de cita.")

    # 2. Pre-check de UX (reutiliza fetch_free_slots, no repite la consulta).
    ...
    if not any(...):
        raise ApiError(409, "slot_unavailable", "Ese horario ya no está disponible.")

    # 3. Lo que de verdad decide: el commit, con su propio try/except si hay una
    # constraint de BD (UNIQUE, EXCLUDE...) que pueda saltar bajo concurrencia.
    ...
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "slot_unavailable", "...") from None
    db.refresh(booking)

    return booking
```

## Checklist al terminar un endpoint

- [ ] Una función, comentarios de paso, sin `_helpers` de un solo uso.
- [ ] Errores de regla de negocio con `raise ApiError(status, code, detail)` — nunca un
      `HTTPException` a mano.
- [ ] `response_model` explícito en el decorador, y `status_code` si no es el 200/201 por
      defecto de FastAPI.
- [ ] `db: Annotated[Session, Depends(get_db)]` — nunca abrir una sesión a mano.
- [ ] Si escribe en BD y hay una constraint que puede saltar bajo concurrencia (`UNIQUE`,
      `EXCLUDE`...): `try/except IntegrityError` + `db.rollback()` + traducir al mismo
      código que ya usa el pre-check, si lo hay.
- [ ] Tests en `tests/test_api_<algo>.py`, con la fixture `api_client` (no `client`) si el
      endpoint toca la base de datos — `tests/test_api_bookings.py` es la plantilla.
- [ ] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app` y
      `uv run pytest` en verde antes de darlo por terminado.

## Errores que ya se cometieron aquí (no los repitas)

- Trocear `create_booking` en `_find_active_appointment_type` / `_ensure_slot_is_free` /
  `_insert_booking` — tres funciones que solo llamaba ese endpoint. Se deshizo: es
  justo el ejemplo de "extracción por estética" que esta skill existe para evitar.
- Volver a hacer la consulta de reglas/excepciones/reservas dentro del endpoint en vez de
  reutilizar `fetch_free_slots` — esa sí hay que compartirla, porque la usan dos rutas.
