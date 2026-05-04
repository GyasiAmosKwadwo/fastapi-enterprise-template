# Backend Template Playbook

This guide shows how to turn this codebase into a reusable GitHub template and how to use it for every new backend project.

## Goal

Use this architecture repeatedly without copy-paste drift, while keeping shared modules like authentication, roles/permissions, and notifications maintainable.

## Architecture Pattern to Keep

This project already follows a strong layered pattern:

1. `API` layer: `app/api/v1/endpoints`
2. `Service` layer: `app/services`
3. `Repository` layer: `app/repositories`
4. `Domain` layer: `app/models` + `app/schemas`
5. `Infrastructure` layer: `app/core`, `app/tasks`, `app/integrations`

Keep this structure as the baseline for all new projects.

## Strategy (Recommended)

Use both:

1. A GitHub template repository for quick project startup.
2. A shared internal package for reusable modules (`auth`, `rbac`, `notifications`).

Why both:

1. Template gives speed.
2. Shared package prevents long-term module drift.

## Phase 1: Prepare This Repo for Template Use

1. Create a cleanup branch.
```bash
git checkout -b chore/template-hardening
```
2. Remove project-specific branding from docs and env values.
3. Add or update `.env.example` with safe placeholders only.
4. Keep default scripts that every project needs:
```bash
make dev
make up
make migrate
make test
```
5. Ensure seed scripts are generic enough for reuse:
```bash
scripts/seed_permissions.py
scripts/create_admin.py
```
6. Commit:
```bash
git add .
git commit -m "chore: harden repo for template usage"
```

## Phase 2: Publish as a GitHub Template

1. Push repository to GitHub.
2. Open repository `Settings`.
3. Enable `Template repository`.
4. Rename repository to something reusable, for example:
`fastapi-enterprise-template`
5. Add topics:
`fastapi`, `template`, `rbac`, `celery`, `postgres`, `redis`

## Phase 3: Create a Shared Core Package

Create a private repo for shared modules, for example `platform-core`.

1. Move reusable code into the package in clear modules:
`platform_core/auth`, `platform_core/rbac`, `platform_core/notifications`
2. Keep business-specific features in each app repo.
3. Version the package with semantic versions:
`v0.1.0`, `v0.2.0`, `v1.0.0`
4. Publish to private package registry (GitHub Packages or internal index).
5. Install it in each new project via `requirements.txt` or `pyproject.toml`.

Example (`requirements.txt`):
```txt
platform-core==0.1.0
```

## Phase 4: Starting a New Project from Template

1. Click `Use this template` on GitHub.
2. Create the new repo, for example `customer-onboarding-api`.
3. Clone it:
```bash
git clone git@github.com:your-org/customer-onboarding-api.git
cd customer-onboarding-api
```
4. Create environment file:
```bash
cp .env.example .env
```
5. Update app metadata:
`APP_NAME`, database name, API keys, hostnames.
6. Start local stack:
```bash
make up
make migrate
make seed
```
7. Run tests:
```bash
make test
```
8. Replace only domain modules for the new project:
`app/models`, `app/services`, `app/api/v1/endpoints` (project-specific parts).
9. Keep shared modules standardized through `platform-core`.

## Update Flow for Shared Modules

When you improve auth/RBAC/notifications:

1. Update shared package repo.
2. Release new version, for example `0.2.0`.
3. Upgrade dependency in each project:
```bash
pip install -U platform-core==0.2.0
```
4. Run tests in each project before merge.

## Suggested Branching Convention

Use this simple model:

1. `main`: stable.
2. `develop`: integration branch.
3. feature branches:
`feat/...`, `fix/...`, `chore/...`

## New Project Bootstrap Checklist

1. Repo created from template.
2. `.env` configured.
3. Database and Redis running.
4. Migrations applied.
5. Base permissions seeded.
6. Admin user created.
7. CI pipeline green.
8. Project-specific endpoints added.

## Common Pitfalls

1. Copying shared modules into each repo instead of using a package.
2. Keeping secrets in template defaults.
3. Mixing project-specific logic into shared modules.
4. Skipping versioning for shared package changes.

## Practical Rule of Thumb

If the logic is reusable in 3 or more projects, move it to `platform-core`.
If it is domain-specific to one product, keep it inside that project repo.
