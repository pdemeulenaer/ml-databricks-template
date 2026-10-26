.DEFAULT_GOAL := help
PORT ?= 8000
UV ?= uv
.PHONY: help install test lint format docs docs-serve docs-build docs-clean example basis-check basis-sync basis-compare
help:
	@printf '%s\n' \
		'install     Sync template maintenance dependencies' \
		'test        Render and verify the template matrix (local only)' \
		'lint        Check maintenance code' \
		'example     Render the classification reference into examples/generated' \
		'basis-check Check the reviewed provenance and generated snapshot' \
		'basis-sync  Copy reviewed provenance into the generated template' \
		'basis-compare Compare installed skills/CLI; requires SKILLS_DIR' \
		'docs        Serve documentation at http://127.0.0.1:$(PORT)' \
		'docs-build  Build documentation and check for warnings' \
		'docs-clean  Remove the generated site directory'
install:
	$(UV) sync --group dev --group docs

test: basis-check
	$(UV) run --group dev pytest

lint:
	$(UV) run --group dev ruff check .
	$(UV) run --group dev ruff format --check .

format:
	$(UV) run --group dev ruff check --fix .
	$(UV) run --group dev ruff format .

example: basis-check
	$(UV) run --group dev copier copy --defaults --data-file examples/classification.yml "$(CURDIR)" examples/generated

basis-check:
	$(UV) run --group dev python scripts/template_basis.py check

basis-sync:
	$(UV) run --group dev python scripts/template_basis.py sync

basis-compare:
	@test -n "$(SKILLS_DIR)" || (printf '%s\n' 'Set SKILLS_DIR to the installed Databricks skills directory.' >&2; exit 2)
	$(UV) run --group dev python scripts/template_basis.py compare --skills-dir "$(SKILLS_DIR)"

docs docs-serve:
	$(UV) run --group docs mkdocs serve -a 127.0.0.1:$(PORT)

docs-build:
	$(UV) run --group docs mkdocs build --strict

docs-clean:
	rm -rf site
