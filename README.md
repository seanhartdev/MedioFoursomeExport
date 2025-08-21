Perfect — here’s the README updated with a **Quickstart** section so it’s GitHub-ready:

---

# MGA Foursome List to CSV

This tool converts a [Mediocre Golf Association](https://mgatour.com) event “Foursome List” page into a structured CSV file.
Each row in the CSV corresponds to **one player**, with columns for:

* **Group** (numeric group number)
* **Time** (tee time, with AM/PM)
* **FirstName**
* **LastName**

---

## Features

* Works with a live URL (e.g. `https://mgatour.com/events/foursome-list/17116`)
* Or with a saved HTML file from the MGA site
* Automatically cleans up group labels, normalizes times, and splits names

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
git clone https://github.com/your-username/mga-foursomes-csv.git
cd mga-foursomes-csv

# install dependencies
pip install -r requirements.txt

# run against a live MGA foursome list
python mga_foursomes_to_csv.py "https://mgatour.com/events/foursome-list/17116" -o foursomes.csv
```

Or run against a saved HTML file:

```bash
python mga_foursomes_to_csv.py ./foursome-list-17116.html -o foursomes.csv
```

---

## Example Output

CSV file (`foursomes.csv`):

```csv
Group,Time,FirstName,LastName
1,9:06AM,Chris,Dohrn
1,9:06AM,Raymond,Major
1,9:06AM,Chad,Johnson
1,9:06AM,Stephen,Seagly
2,9:15AM,Timothy,Gunn
2,9:15AM,Nick,Gunn
2,9:15AM,douglas,leitch
...
```

---

## Notes

* Groups are always stored as **numbers** (e.g. `1` instead of `Group 1`).
* Time keeps its **AM/PM** suffix (e.g. `9:06AM`).
* Name splitting is done on the **first space**. Multi-word last names will all go into the `LastName` column.
* Sorting is **by Group → Time → LastName**.

---

