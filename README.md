# PhishGuard

**ML-Based Phishing URL & Website Detector**

PhishGuard is a small machine-learning project that analyzes URL characteristics and predicts whether a URL appears legitimate or potentially phishing-related. It has a training script, a prediction module, a Flask web interface, and automated tests.

## Quick Start

Windows 10/11, PowerShell, Python 3.11+.

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt
```

If PowerShell says *"running scripts is disabled on this system"*, run this once (it only affects your user account and still blocks unsigned scripts downloaded from the internet), then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or activate from Command Prompt with `.venv\Scripts\activate.bat`, or skip activation and call `.venv\Scripts\python.exe` directly.

```powershell
# 3. Get the dataset (see data\raw\README.md), then place it at:
#    data\raw\PhiUSIIL_Phishing_URL_Dataset.csv

# 4. Train the model (prints real metrics and saves models\phishing_model.joblib)
python src\train_model.py

# 5. Start the web app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

Run the tests:

```powershell
pytest
```

## About

Given a URL, PhishGuard:

1. validates it (it never visits the URL),
2. extracts numeric features from the URL text,
3. passes them through a trained scikit-learn model,
4. reports a phishing probability, a label and a risk level,
5. lists simple structural indicators found in the URL.

The result is an estimate. It cannot guarantee that a website is safe or malicious.

## Why I Built This

<!-- Edit this section so it reflects your own reasons. Keep it factual. -->
PhishGuard is a learning project that combines machine learning with defensive cybersecurity. It covers the full path from raw data to a working application: data cleaning, feature engineering, model comparison, prediction, a web interface, and testing.

## Features

- URL validation with clear error messages
- 29 URL-based features (length, character counts, hostname structure, IP detection, keywords, and more)
- Two models compared on real data: Logistic Regression and Random Forest
- Hostname-grouped train/test split to reduce data leakage
- Flask web interface with prediction, risk level, probability and detected indicators
- Heuristic indicators shown separately from the ML prediction
- Automated tests with pytest

## How It Works

```text
User enters URL
      |
URL validation              src/utils.py
      |
Feature extraction          src/feature_extractor.py
      |
DataFrame with fixed        src/preprocessing.py
column order
      |
Scikit-learn Pipeline       models/phishing_model.joblib
(trained model)
      |
Phishing probability        src/predictor.py
      |
Label + risk level  ---+--- Heuristic indicators (rules, separate from the model)
      |
JSON response               app.py
      |
Browser                     templates/index.html, static/script.js
```

**Risk level.** The phishing probability *p* from the model is mapped like this (`src/predictor.py`):

| Probability | Prediction | Risk level |
|---|---|---|
| p < 0.35 | Legitimate | Low |
| 0.35 <= p < 0.65 | Suspicious | Medium |
| p >= 0.65 | Potentially Phishing | High |

These cut-offs are simple choices for this project. They were not tuned and are not an industry-standard score. Random Forest probabilities in particular are not calibrated, so "0.80" does not mean "80% of such URLs are phishing".

## Project Architecture

```text
PhishGuard/
|-- app.py                     Flask routes (GET /, POST /analyze)
|-- requirements.txt
|-- pytest.ini
|-- README.md, LICENSE, .gitignore, .env.example
|-- data/
|   |-- raw/README.md          Where to download the dataset
|   `-- processed/
|-- models/                    Trained model is saved here (not committed)
|-- src/
|   |-- feature_extractor.py   URL -> numeric features, plus indicators
|   |-- preprocessing.py       Load/clean data, split, build pipeline
|   |-- train_model.py         Train, evaluate, compare, save
|   |-- predictor.py           Load model, predict, risk level
|   `-- utils.py               Paths, errors, URL validation, IP check
|-- templates/index.html
|-- static/style.css, static/script.js
`-- tests/
    |-- test_features.py       Validation and feature extraction
    |-- test_predictor.py      Prediction pipeline and errors
    |-- test_preprocessing.py  Cleaning, splitting, dataset loading
    |-- test_app.py            Flask routes
    `-- toy_model.py           Tiny throwaway model used only by tests
```

## Technologies

Python 3.11+, Flask, pandas, NumPy, scikit-learn, joblib, pytest, HTML/CSS/JavaScript. URL parsing uses only the Python standard library (`urllib.parse`, `ipaddress`, `re`).

## Dataset

**PhiUSIIL Phishing URL Dataset** — Arvind Prasad and Shalini Chandra, UCI Machine Learning Repository (dataset id 967). Paper: *PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning*, Computers & Security, 2024 (doi: 10.1016/j.cose.2023.103545).

- Size (as published): 235,795 URLs, 134,850 legitimate and 100,945 phishing
- Label meaning: `1` = legitimate, `0` = phishing
- License: see the license shown on the UCI dataset page
- The CSV is not committed. See [`data/raw/README.md`](data/raw/README.md) for download steps.

PhishGuard uses only the `URL` and `label` columns. The dataset's other columns (including some derived from page HTML) are ignored, because PhishGuard computes its own features from the URL text.

**Preprocessing** (`clean_dataset` in `src/preprocessing.py`), with the counts printed each time you train:

1. drop rows with a missing URL or label
2. drop labels other than 0/1
3. drop URLs that fail validation
4. drop URLs that appear with conflicting labels
5. drop duplicate URLs
6. convert labels so that `is_phishing = 1` means phishing

## Feature Engineering

All features are computed locally from the URL string. No feature is proof of anything: each one is only a hint, and the model combines them.

| Feature | Measures | Why it may matter | Limitation |
|---|---|---|---|
| `url_length` | Characters in the URL | Very long URLs can hide the real destination | Legitimate sites also use long URLs |
| `num_special_chars`, `num_hyphens`, `num_dots`, `num_slashes`, ... | Counts of individual characters | Unusual structure can differ between phishing and normal URLs | Depends on how the dataset was collected |
| `digit_ratio` | Share of characters that are digits | Random-looking or numeric URLs | Tracking IDs in legitimate URLs contain digits |
| `hostname_length`, `hostname_num_hyphens`, `hostname_num_digits` | Shape of the hostname | Long hyphenated names imitate brands (e.g. `secure-login-...`) | Some real brands use hyphens |
| `num_subdomains` | Labels left of the registered domain (`www` counts) | Many subdomains can bury the real domain | Only a small hand-written list of two-part suffixes like `co.uk` is handled |
| `is_ip_hostname` | Hostname is an IPv4/IPv6 address (checked with `ipaddress`, not by looking for digits) | Real sites rarely use raw IPs | Internal tools and test servers also do; encoded IPs like `http://3232235521` are not detected |
| `hostname_is_idn` | Hostname has `xn--` or non-ASCII characters | Look-alike (homograph) domains | Many legitimate international domains use it |
| `is_shortener` | Hostname is in a short list of URL shorteners | Hides the destination | Shortened links are common and mostly harmless |
| `uses_https` | Scheme is HTTPS | Missing HTTPS is a weak warning sign | Many phishing sites use HTTPS too |
| `has_at_symbol` | `@` in the URL | Text before `@` can disguise the real host | Rare in practice, but appears in some legitimate URLs |
| `has_explicit_port` | Non-default port | Unusual for public websites | Common in development and internal services |
| `num_path_segments`, `num_query_params` | Path depth and query size | Deeply nested or parameter-heavy URLs | Web apps use both legitimately |
| `num_encoded_chars`, `has_double_slash_in_path` | `%XX` escapes and `//` in the path | Used to obfuscate URLs | Also normal in legitimate URLs |
| `num_suspicious_keywords` | Count of words like `login`, `verify`, `account`, `secure`, `update`, `password`, `banking`, `signin`, `confirm` (substring match) | Common in phishing lures | Banks and email providers use the same words; substrings can match harmless words |

Edit the keyword list, shortener list and suffix list at the top of `src/feature_extractor.py`.

## Machine Learning

Classical models suit this problem because the input is a small table of numeric features.

- **Logistic Regression** (with `StandardScaler`): simple, fast and easy to interpret through its coefficients.
- **Random Forest**: can capture non-linear interactions between features and needs no scaling.

Both use class weighting because the classes are not perfectly balanced. Both are wrapped in a scikit-learn `Pipeline`, so the exact same preprocessing runs during training and prediction. The scaler is fitted on the training set only.

**Split.** 80% train / 20% test, grouped by hostname (`GroupShuffleSplit`) so the same website never appears in both sets. A plain random split would let the model see `example.com/page1` in training and be tested on `example.com/page2`, which inflates the score.

**Model selection** (`select_final_model` in `src/train_model.py`): choose the model with the highest F1 on the phishing class in the test set. If Random Forest wins by 0.005 or less, Logistic Regression is kept because it is simpler and easier to explain. The script prints the reason for its choice.

## Evaluation

Run `python src\train_model.py` to generate your own numbers. They are printed and also saved to `models/metrics.json`. Metrics use **phishing as the positive class**.

| Metric | Meaning |
|---|---|
| Accuracy | Share of all predictions that were correct. Can look good even when one class is handled badly. |
| Precision | Of the URLs flagged as phishing, how many really were. Low precision means many false alarms. |
| Recall | Of all real phishing URLs, how many were caught. Low recall means missed phishing. |
| F1-score | Harmonic mean of precision and recall. |
| Confusion matrix | Counts of true/false positives and negatives. |

- **False positive:** a legitimate URL flagged as phishing. Users lose trust and start ignoring warnings.
- **False negative:** a phishing URL passed as legitimate. A user may be harmed. Usually the costlier error.

Both matter, which is why the project reports precision and recall and does not select on accuracy alone.

**Your results** (fill in after training; do not copy numbers from anywhere else):

| Model | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|
| Logistic Regression | | | | |
| Random Forest | | | | |

Very high scores on this dataset should be treated with caution. Public datasets are often collected in a way that makes the two classes look different from real-world traffic, so a model can score well by learning collection artifacts. Check the "Top features" list printed after training to see what the model relied on.

## Installation

See **Quick Start**. Requirements: Windows 10/11, Python 3.11+, PowerShell. No Docker, WSL or cloud services are needed.

## Dataset Setup

1. Download the dataset as described in [`data/raw/README.md`](data/raw/README.md).
2. Save the CSV as `data\raw\PhiUSIIL_Phishing_URL_Dataset.csv`.

## Training

```powershell
python src\train_model.py
```

Optional: `python src\train_model.py --data "C:\path\to\dataset.csv"`

The script loads and inspects the data, cleans it, extracts features, splits by hostname, trains both models, prints train and test metrics with confusion matrices, selects a model, and saves `models\phishing_model.joblib` and `models\metrics.json`. The model file is generated locally and is not committed.

## Running the Application

```powershell
python app.py
```

Open http://127.0.0.1:5000. The server listens only on your own computer (`127.0.0.1`). If the model has not been trained, the page shows: *Model file not found. Please train the model first: `python src\train_model.py`*.

## Testing

```powershell
pytest
```

The tests cover URL validation, feature extraction (including IPv4/IPv6 and the "digits in a domain are not an IP" case), dataset cleaning, the prediction pipeline (missing, corrupted and outdated model files), and the Flask routes. Tests that need a model train a tiny throwaway one in a temporary folder, so they run without the real dataset and do not measure model quality.

## Example

Structural test input using a reserved documentation address (`192.0.2.0/24`), which is safe to use in demos:

```text
http://192.0.2.10/login/verify/account
```

Indicators detected for this URL:

```text
- IP address used in the hostname instead of a domain name
- Contains words often seen in phishing URLs: login, verify, account
- Does not use HTTPS
```

The probability, label and risk level come from your trained model, so they depend on your training run. The indicators are rule-based and do not change the model's probability, so the two can disagree; that is expected.

Response shape of `POST /analyze`:

```json
{
  "ok": true,
  "result": {
    "url": "https://example.com",
    "prediction": "Legitimate",
    "phishing_probability": 0.0,
    "confidence": 1.0,
    "risk_level": "Low",
    "indicators": [],
    "model_name": "..."
  }
}
```

(Values above are only illustrative of the format.)

## Limitations

- A URL classifier cannot guarantee that a site is safe.
- Legitimate URLs can look suspicious, and phishing URLs can look normal.
- Dataset quality limits performance, and the dataset may differ from real-world traffic.
- New attack patterns may not exist in the training data.
- Real-world performance may differ from test-set performance.
- A model probability is not proof, and Random Forest probabilities are not calibrated.
- Only the URL text is analyzed. The page content, certificate, domain age and reputation are not checked.
- Attackers can change URL structure to avoid these features.
- The keyword and shortener lists are small and hand-made.
- Only English-language keywords are checked.

## Future Improvements

Ideas, none implemented: browser extension, domain-reputation or DNS/WHOIS features (optional, with fallbacks), explainable ML for individual predictions, probability calibration, a larger and more recent dataset, retraining and monitoring, robustness tests against URL obfuscation.

## Security Notice

PhishGuard is defensive and educational. It does not create phishing pages, collect credentials, or visit submitted URLs. It only analyzes the text of a URL locally.

- Model files (`.joblib`) are Python pickles. Only load model files you trained yourself.
- User input is validated, and results are rendered with `textContent` so a crafted URL cannot inject HTML.
- The server binds to `127.0.0.1` with Flask debug mode off. Do not expose it publicly without a production server, HTTPS and rate limiting.
- Use only harmless inputs (such as `https://example.com` or the `192.0.2.x` documentation range) when demonstrating.
- Never commit `.env` files or API keys.
