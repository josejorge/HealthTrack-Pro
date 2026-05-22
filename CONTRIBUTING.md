# Contribuir a HealthTrack Pro

¡Gracias por considerar contribuir a HealthTrack Pro!
Este documento explica el proceso para hacer contribuciones de calidad.

---

## Proceso de contribución

1. **Fork** el repositorio en GitHub
2. Crea una rama desde `develop`:
   ```bash
   git checkout -b feature/mi-nueva-funcionalidad
   ```
3. Escribe código con pruebas
4. Asegúrate de que todos los tests pasan:
   ```bash
   pytest tests/ -v
   ```
5. Formatea el código:
   ```bash
   black .
   ruff check . --fix
   ```
6. Haz commit siguiendo la convención:
   ```bash
   git commit -m "feat(modulo): descripción en español"
   ```
7. Crea un Pull Request hacia `develop`

---

## Estándares de código

- Todo el código, comentarios y mensajes en **español**
- Type hints obligatorios en métodos públicos
- Docstring en todos los métodos públicos
- Tests para cualquier nueva funcionalidad o corrección de bug
- Sin `TODO` vacíos — si algo no está implementado, abre un issue

---

## Reportar bugs

Al reportar un bug incluye:
- Versión de HealthTrack Pro (`python main.py --version`)
- Sistema operativo y versión de Python
- Pasos para reproducir
- Comportamiento esperado vs. real
- Logs relevantes de `logs/errores.log`

---

## Código de conducta

Este proyecto sigue el [Contributor Covenant](https://www.contributor-covenant.org/).
Sé respetuoso, constructivo y profesional en todas las interacciones.
