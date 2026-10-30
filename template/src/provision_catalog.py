# Databricks notebook source
"""Create the configured catalog using the workspace's default managed storage."""

import re

dbutils.widgets.text("catalog", "")  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # noqa: F821
if not re.fullmatch(r"[a-z][a-z0-9_]*", catalog):
    raise ValueError("Catalog must be a lowercase SQL identifier")

# This SQL runs in the serverless workspace so Databricks can choose default storage.
# IF NOT EXISTS makes retries and subsequent deployments safe for the same catalog.
spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")  # noqa: F821
