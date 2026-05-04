# Backend Template Playbook

This guide shows how to turn this codebase into a reusable GitHub template and how to use it for every new backend project.

## Goal

Use this architecture repeatedly without copy-paste drift, while keeping shared modules like authentication, roles/permissions, and notifications maintainable.

## Architecture Pattern to Keep

This project follows a layered pattern:

1. `API` layer: `app/api/v1/endpoints`
2. `Service` layer: `app/services`
3. `Repository` layer: `app/repositories`
4. `Domain` layer: `app/models` + `app/schemas`
5. `Infrastructure` layer: `app/core`, `app/tasks`, `app/integrations`

## Strategy (Recommended)

Use both:

1. A GitHub template repository for quick project startup.
2. A shared internal package for reusable modules (`auth`, `rbac`, `notifications`).

Why both:

1. Template gives speed.
2. Shared package prevents long-term module drift.

## Maintenance Model

Template inheritance gives you a starting snapshot. It does not auto-sync later changes.

Use this split:

1. Inherited once from template: `docker-compose.yml`, Makefile commands, base folder structure, CI workflow skeleton.
2. Centrally maintained across projects: auth, RBAC, notifications, and shared infra helpers via a versioned shared package.

## Phase 1: Prepare This Repo for Template Use

1. Create a cleanup branch.
```bash
git checkout -b chore/template-hardening
```
2. Remove project-specific branding from docs and env values.
3. Add or update `.env.example` with safe placeholders only.
4. Keep default scripts every project needs: `make dev`, `make up`, `make migrate`, `make test`.
5. Ensure seed scripts are generic enough for reuse.
6. Commit.

## Domain Cleanup Pass (Important)

Before publishing the template, remove or rename any domain-specific modules you do not want in every new project.

Common candidates in this repo:

1. `app/integrations/ghana_card.py`
2. `app/integrations/ghana_post_gps.py`
3. `app/integrations/xds_data.py`
4. `app/models/vettingForm.py`
5. Domain-focused workflow routes/services tied to vetting/background checks

After removing modules, also update:

1. `app/api/v1/router.py` imports
2. `app/tasks/*` task includes
3. `requirements.txt` for unused dependencies

## Phase 2: Publish as a GitHub Template

1. Push repository to GitHub.
2. Open repository `Settings`.
3. Enable `Template repository`.
4. Rename repository to something reusable, for example `fastapi-enterprise-template`.
5. Add topics: `fastapi`, `template`, `rbac`, `celery`, `postgres`, `redis`.

## Phase 3: Create a Shared Core Package

Create a private repo for shared modules, for example `platform-core`.

1. Move reusable code into modules such as `platform_core/auth`, `platform_core/rbac`, `platform_core/notifications`.
2. Keep business-specific features in each app repo.
3. Version the package using semantic versions.
4. Publish to private package registry (GitHub Packages or internal index).
5. Install it in each new project via `requirements.txt` or `pyproject.toml`.

## Phase 4: Starting a New Project from Template

1. Click `Use this template` on GitHub.
2. Create the new repo.
3. Clone it and copy env file.
```bash
git clone git@github.com:your-org/your-new-api.git
cd your-new-api
cp .env.example .env
```
4. Update app metadata and environment variables.
5. Start local stack and migrations.
```bash
make up
make migrate
make seed
```
6. Run tests.
```bash
make test
```

## New Project Bootstrap Checklist

1. Repo created from template
2. `.env` configured
3. Database and Redis running
4. Migrations applied
5. Base permissions seeded
6. Admin user created
7. CI pipeline green
8. Project-specific endpoints added
