
# Project Folder Structure

```text
ssd_test/
├── App/
│   ├── ssd_test.py
│   ├── ssd_inventory.csv
│   └── requirements.txt
├── Docs/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   └── FOLDERS.md
├── Tests/
│   └── test_ssd_test.py
├── Reports/
│   ├── .gitkeep
│   ├── inventory.csv
│   ├── _archive/
│   │   └── SERIAL_TIMESTAMP/
│   │       ├── report.pdf
│   │       ├── execution.log
│   │       └── dd.log
│   └── SERIAL_NUMBER/
│       ├── report.pdf
│       ├── execution.log
│       ├── dd.log
│       └── opal_recovery.txt (only if retained)
├── .venv/
├── .gitignore
└── README.md
```

## Directory Responsibilities

- `App/`: Python application, dependencies, and source inventory.
- `Docs/`: Requirements, architecture, and project structure.
- `Tests/`: Automated software tests.
- `Reports/`: SSD reports, verification results, processing logs, and archived records.
- `.venv/`: Local Python virtual environment.

`opal_recovery.txt` contains a temporary Opal administrator credential if recovery is required. It is created with owner-only permissions.

`Reports/` and `.venv/` are excluded from version control.
