---

# MGA Foursome Export

This tool exports a the player groups in an [Mediocre Golf Association](https://mgatour.com) event to a CSV file.

---

## Features

* Works with a live URL (e.g. `https://[EVENT_PAGE_ADDRESS]`)
* Or with a saved HTML file from the MGA site
* Splits names into first and last

---

## Requirements

* Python **3.8+**
* Packages:

  * [`requests`](https://pypi.org/project/requests/)
  * [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

Install dependencies with:

```bash
pip install requests beautifulsoup4
```

---

## Quickstart

Clone the repo and run the tool:

```bash
git clone https://github.com/seanhartdev/MedioFoursomeExport.git
cd MedioFoursomeExport

# install dependencies
pip install -r requirements.txt

# run against a live MGA foursome list
python  medio_foursome_export.py "https://[EVENT_PAGE_ADDRESS]" -o foursomes.csv
```

Or run against a saved HTML file:

```bash
python medio_foursome_export.py ./foursome-list-17116.html -o foursomes.csv
```



