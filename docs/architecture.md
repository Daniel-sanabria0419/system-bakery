# Architecture — Beta 1

## Objetivo

La arquitectura debe permitir construir una aplicación de escritorio sencilla actualmente y poder evolucionarla posteriormente sin tener que reescribir completamente el proyecto.

## Arquitectura general

```text
PySide6 / Qt
      |
      v
Aplicación local
      |
      v
FastAPI
      |
      v
Lógica de aplicación
      |
      v
Persistencia
      |
      v
SQLite