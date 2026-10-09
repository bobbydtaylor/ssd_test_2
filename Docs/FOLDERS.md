
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
│   └── SERIAL_NUMBER/
│       ├── report.pdf
│       └── execution.log
├── .venv/
├── .gitignore
└── README.md
```

## Directory Responsibilities

- `App/`: Application code, dependencies, and SSD source inventory.
- `Docs/`: Requirements, architecture, and project structure.
- `Tests/`: Automated software tests.
- `Reports/`: Generated test results, PDF reports, and logs.
- `.venv/`: Local Python virtual environment.

`Reports/` and `.venv/` contain generated or local files excluded from version control.
