
# Understanding Your SSD Testing Project — Python Explained

Your SSD testing project is a **Python application that automates work you could otherwise perform manually using Ubuntu commands**.

Instead of typing individual commands to identify an SSD, test it, erase it, verify it, and produce a report, you run one Python program that coordinates those operations.

You do not need to be a Python programmer to operate it.

## 1. What is Python?

Python is a programming language, similar in purpose to C, C++, or PowerShell.

The main difference is that Python is generally interpreted: you write a text file containing Python instructions and use the Python interpreter to execute them.

For example:

```python
print("SSD Test Started")
```

When you run that program, Python displays:

```text
SSD Test Started
```

Unlike a typical C application, you do not need to compile your Python source code into an executable before running it.

Your application's main source file is:

`App/ssd_test.py`

The `.py` extension identifies it as a Python source file.

## 2. How your project is organized

Your existing project contains:

```text
ssd_test/
├── App/
├── Docs/
├── Tests/
├── Reports/
├── .venv/
└── README.md
```

- `App/` — The working Python application and SSD inventory.
- `Docs/` — Requirements, architecture, and project documentation.
- `Tests/` — Automated checks of the Python code.
- `Reports/` — SSD results, PDF reports, and processing logs.
- `.venv/` — The project's private Python environment.
- `README.md` — Instructions for setting up and operating the application.

This is an engineering project:

- `App/` is the implementation.
- `Docs/` is the engineering documentation.
- `Tests/` is the software test bench.
- `Reports/` is the output from actual SSD testing.

## 3. What is a virtual environment, and why do we need one?

This is probably the most important Python-specific concept to understand.

When Ubuntu installs Python, it installs a system-level Python interpreter. Ubuntu and other applications may depend on specific versions of Python packages.

Your SSD application uses an additional Python package called **ReportLab** to generate PDF reports.

Installing packages directly into Ubuntu's system Python can cause conflicts with packages managed by Ubuntu.

A virtual environment avoids that.

### Ubuntu Python

Managed by the operating system and shared with system tools.

System Python packages.

### Project `.venv`

Dedicated Python environment with packages installed for this application.

ReportLab and dependencies.

Think of a virtual environment as a **private toolbox for one project**.

It does not create a virtual computer or a virtual machine. It simply keeps the Python interpreter and project-specific Python packages organized and isolated.

### Creating the virtual environment

From the project directory:

```bash
python3 -m venv .venv
```

This creates a folder named `.venv`.

You normally do this only once.

### Installing ReportLab

Next:

```bash
.venv/bin/python -m pip install -r App/requirements.txt
```

Here's what each part means:

| Command portion | Meaning |
|---|---|
| `.venv/bin/python` | Use this project's Python interpreter |
| `-m pip` | Run Python's package installer |
| `install` | Install the required packages |
| `-r App/requirements.txt` | Read the package requirements from that file |

Your `requirements.txt` currently specifies:

```text
reportlab>=4.4,<5
```

That tells Python to install ReportLab version 4.4 or newer, but not version 5.

This is how we keep the project's Python dependencies consistent without interfering with Ubuntu.

**You do not need to recreate the virtual environment each time you use the application.**

## 4. What does the Python application actually do?

Your Python program acts as the coordinator.

It calls existing Linux programs, evaluates their output, makes decisions, and documents the results.

```text
You start the Python application
          |
          v
      ssd_test.py
          |
          v
Python coordinates Linux utilities
lsblk | nvme | dd | sedutil-cli | parted
          |
          v
The utilities communicate with the SSD
Identify | Test | Sanitize | Verify
          |
          v
Python evaluates and records results
PDF report | CSV summary | Execution log
```

Python itself is not performing every hardware operation. For example, it tells Linux to run `dd` to overwrite the SSD and then performs its own readback verification.

This is a common approach in engineering automation.

## 5. What happens when you start the application?

You have two operating modes.

### Mode A — Preflight (read-only)

```bash
sudo .venv/bin/python App/ssd_test.py
```

Let's decode this command:

| Part | Meaning |
|---|---|
| `sudo` | Run with administrator privileges |
| `.venv/bin/python` | Start the project's Python interpreter |
| `App/ssd_test.py` | Execute your application's main file |

The program checks that the SSD is installed, recognized, and matches your inventory.

It does not erase anything.

This is similar to performing a preflight inspection on an engineering test bench.

### Mode B — Full processing

```bash
sudo .venv/bin/python App/ssd_test.py --execute
```

The additional `--execute` flag tells the application to perform the actual testing and sanitization operations.

That flag is something we programmed into your application. It is not a built-in Python command.

### What happens during processing?

1. **Identify the SSD**

   Read its model, serial number, and capacity. Compare that information with your inventory.

2. **Check SSD health**

   Read SMART information and run the built-in NVMe short self-test.

3. **Overwrite the SSD**

   Use the Linux `dd` utility to write zeros across its entire accessible storage capacity.

4. **Verify the overwrite**

   Read every accessible byte and confirm the data reads as zero.

5. **Perform the Opal reset**

   Initialize the SSD's Opal security system, then perform the authenticated Revert operation.

6. **Verify and report**

   Confirm the reset state, check final health, and save the processing results.

The application follows the same general workflow you previously performed manually at the Ubuntu command line.

## 6. What happens when something goes wrong?

Python can make decisions based on the results of each operation.

For example, if the SSD fails its SMART health check, the application stops instead of proceeding with normal processing.

Or if Ubuntu cannot find an NVMe device, Python displays:

```text
ERROR: Expected one onboard NVMe SSD; found 0
```

That's the error you encountered with SSD serial number ending in `1853`.

The application correctly refused processing because Ubuntu did not detect that drive.

The Python program cannot repair hardware failures; it can identify conditions that prevent the test from proceeding.

## 7. What is the purpose of the `Tests/` folder?

The file:

`Tests/test_ssd_test.py`

contains automated tests of your Python source code.

For example, one test deliberately supplies invalid inventory data and verifies that the application rejects it.

Another creates a small file containing zeros and confirms that the verification function accepts it. It also checks that nonzero data causes a failure.

When you run:

```bash
.venv/bin/python -m unittest discover -s Tests -v
```

Python finds the unit tests, runs them, and reports their results.

These tests do **not** erase a physical SSD. They test portions of the application's logic.

Think of them as software-level bench tests before performing the real hardware procedure.

## 8. What is the difference between `requirements.txt` and `REQUIREMENTS.md`?

Their names look similar, but their purposes are completely different.

| File | Purpose |
|---|---|
| `App/requirements.txt` | Tells Python which additional software packages to install |
| `Docs/REQUIREMENTS.md` | Describes what your SSD testing application must accomplish |

Similarly, `ARCHITECTURE.md` describes how the application is designed, while `README.md` tells someone how to set it up and operate it.

## 9. What you actually do each day

Once the computer has been set up and the virtual environment exists, your routine is straightforward.

1. Install an SSD with the computer powered off.
2. Boot Ubuntu.
3. Open a terminal in the project directory.
4. Run the preflight command.
5. Run the processing command.
6. Review the resulting PDF.
7. Shut down and swap the SSD.

You do not need to manually activate the virtual environment because the commands explicitly use `.venv/bin/python`.

### The three commands worth remembering

**Check the application**

Read-only preflight:

```bash
sudo .venv/bin/python App/ssd_test.py
```

**Process the SSD**

Destructive testing and sanitization:

```bash
sudo .venv/bin/python App/ssd_test.py --execute
```

**Check the Python code**

Run automated software tests:

```bash
.venv/bin/python -m unittest discover -s Tests -v
```

**The main concept:** Python is the automation engine, Linux supplies the hardware utilities, the virtual environment manages Python dependencies, and your project combines everything into one repeatable SSD testing and sanitization process.

Once the initial setup is complete, you generally operate the application using just the preflight and processing commands.
