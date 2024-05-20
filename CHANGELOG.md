# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Feat: Support custom logger names for `log_if_fails` decorator

## [0.4.1] - 2024-2-1

- Fix: Fix submodule usage detection when installed as an embedded dependency
- Fix: Consider only external calls when detecting plugin path

## [0.4.0] - 2024-1-24

- Feature: New method `resources.load_ui_from_file()` to load a ui file from direct filepath
- Feature: Support subplugins. In some special cases it is wanted to include a plugin inside another. Now `resources.plugin_path()` supports this.
- Fix: Change the implementation of `resources.package_file()` to support Python 3.8
- Refactor: Changed the plugin identification logic used in `resources.plugin_path()`
- Maintenance: Updated development dependencies
- Maintenance: Test on three latest LTR release. That means we drop support for QGIS 3.16.

## [0.3.2] - 2023-11-29

- Fix: Recover from `TypeError` when getting plugin path. Enables pytest-xdist usage.

## [0.3.1] - 2023-08-08

- Feature: Add `exc_info` and `stack_info` parameters to message bar logger for capturing exception.

## [0.3.0] - 2023-03-14

- Feature: Add api to safely load package files
- Maintenance: Updated development dependencies
- Maintenance: Added automatic release actions

## [0.2.0] - 2022-05-12

## [0.1.0] - 2022-03-17
