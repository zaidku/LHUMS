# Flask User Management Service (UMS) - Copilot Instructions

## Project Overview
This is a Flask-based User Management Service that provides centralized user authentication and management for multiple labs in a Django webapp portal.

## Tech Stack
- Flask - Web framework
- Flask-JWT-Extended - JWT authentication
- SQLAlchemy - ORM for database operations
- Marshmallow - Object serialization/deserialization
- Flask-Migrate - Database migrations

## Project Structure
- `app/` - Main application package
  - `models/` - SQLAlchemy models
  - `schemas/` - Marshmallow schemas
  - `routes/` - API blueprints
  - `utils/` - Utility functions
- `config/` - Configuration files
- `migrations/` - Database migration files
- `tests/` - Unit and integration tests

## Development Guidelines
- Follow RESTful API conventions
- Use JWT tokens for authentication
- Implement role-based access control
- Support multi-tenant (lab) architecture
- Validate all inputs using Marshmallow schemas
- Handle errors gracefully with proper HTTP status codes
