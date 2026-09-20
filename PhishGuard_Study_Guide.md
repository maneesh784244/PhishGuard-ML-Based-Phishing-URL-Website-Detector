# PhishGuard Study Guide

This guide is for you, not for the repository. It is written against the code as delivered. Where an answer depends on numbers from *your* training run, it says so. Never quote a number you did not see on your own screen.

---

## 1. Before you present or publish

- [ ] Put your name in `LICENSE`.
- [ ] Download the dataset and check its license on the UCI page; make sure the `Dataset` section of the README is accurate.
- [ ] Run `python src\train_model.py` and fill in the results table in the README from your real output (or from `models\metrics.json`).
- [ ] Look at the "Top features" list printed after training. Be ready to say what the model relied on and whether that makes sense.
- [ ] Run `pytest` and confirm it passes on your machine.
- [ ] Edit the "Why I Built This" README section so it is genuinely in your own words.
- [ ] Read every file at least once. If you cannot explain a line, simplify it or ask.

---

## 2. Live demo (about 5 to 10 minutes)

1. **VS Code**: open the `PhishGuard` folder and walk through the structure (`app.py`, `src/`, `tests/`, `templates/`, `static/`).
2. **`src/feature_extractor.py`**: show `FEATURE_NAMES`, `extract_features`, `count_subdomains`, and the IP check in `src/utils.py` (`ipaddress`, not "contains digits").
3. **`src/train_model.py`**: show cleaning, the hostname-grouped split, the two models, `select_final_model`.
4. **PowerShell**: run `python src\train_model.py` (or show output from an earlier run if time is short). Point at the confusion matrix, train vs test scores and the selection reason.
5. **`src/predictor.py`**: `analyze_url` follows validate, extract, `features_to_frame`, `predict_proba`, `probability_to_result`, `get_indicators`.
6. **PowerShell**: `python app.py`.
7. **Browser**: open http://127.0.0.1:5000.
8. Enter `https://example.com`, click **Analyze URL**, explain each part of the result.
9. Enter `http://192.0.2.10/login/verify/account` (reserved documentation address). Explain that indicators are rules and the probability is the model's; they are independent and can disagree. **Do not promise what the model will say for this URL. Say what you see.**
10. Show a bad input (`example.com`) to demonstrate the error message, and optionally `pytest`.

Use only harmless inputs during a demo. Never use real malicious URLs.

---

## 3. Machine-learning concepts in plain language

- **Dataset**: a table of examples. Here each row is a URL and a label.
- **Label**: the correct answer for each row. In PhiUSIIL, `1` = legitimate and `0` = phishing. PhishGuard flips this to `is_phishing` (1 = phishing) so that "positive" means "the thing we want to catch".
- **Features**: numbers computed from each URL (length, dots, is it an IP, ...). The model only sees these numbers, never the raw text.
- **Classification**: predicting a category (phishing or not) rather than a number.
- **Training set / test set**: the model learns from the training set. The test set is held back to measure how well it does on data it has never seen.
- **Probability**: `predict_proba` gives a number between 0 and 1 for each class. It is the model's estimate, not proof. Random Forest probabilities in particular are not calibrated.
- **Precision**: of everything flagged as phishing, what fraction really was. Low precision means many false alarms.
- **Recall**: of all real phishing URLs, what fraction was caught. Low recall means phishing slips through.
- **F1-score**: one number combining precision and recall (harmonic mean).
- **Confusion matrix**: a 2x2 table of true negatives, false positives, false negatives and true positives.
- **Overfitting**: the model memorizes the training data and does worse on new data. Signal: train score much higher than test score. The training script prints both so you can check.
- **Data leakage**: information from the test set sneaking into training, making results look better than they are. PhishGuard guards against it by fitting the scaler inside a `Pipeline` on training data only, removing duplicate/conflicting URLs, and splitting by hostname.
- **Class imbalance**: one class is more common. The published dataset has roughly 57% legitimate and 43% phishing, which is mild. Both models use class weights. Accuracy alone can hide problems when classes are imbalanced.

## 4. Cybersecurity concepts in plain language

- **Phishing**: tricking someone into giving up credentials or money, often with a fake page that imitates a trusted site.
- **URL structure**: `https://login.example.com:8443/path/page?x=1` = scheme, subdomain, registered domain, port, path, query.
- **Suspicious traits** (hints, never proof): very long URLs, many subdomains, an IP instead of a domain, `@` in the URL, look-alike (punycode) domains, urgent-sounding words, hidden destinations.
- **IP-based URLs**: legitimate public websites rarely use a raw IP, but test servers and internal tools do.
- **URL shortening**: hides the destination. Mostly harmless on its own.
- **False positive / false negative**: see README. In a security tool a false negative is usually the costlier error, but too many false positives make people ignore the tool.
- **Limits of URL-only analysis**: it never looks at the page, certificate, domain age or reputation. A phishing page on a compromised legitimate domain can have a perfectly normal-looking URL.

## 5. Flask concepts in plain language

- **Flask app**: `app = Flask(__name__)` creates the web application object.
- **Route**: a URL path connected to a Python function (`@app.get("/")`, `@app.post("/analyze")`).
- **GET vs POST**: GET asks for a page. POST sends data (here, the URL to analyze) in the request body.
- **Request / response**: the browser sends a request; the function returns a response (HTML for `/`, JSON for `/analyze`).
- **Template**: `templates/index.html` is rendered by `render_template`. It shows a warning banner if the model file is missing.
- **Static files**: `static/style.css` and `static/script.js` are served as-is.
- **Frontend-backend communication**: `script.js` calls `fetch("/analyze", {method: "POST", body: JSON})`. Flask calls `analyze_url`, and returns JSON. The script shows the result, using `textContent` so user input is never treated as HTML.

---

## 6. Interview questions and answers

These are grounded in the code. Adapt the wording so it sounds like you.

**1. What is phishing?**
An attack that tricks people into revealing credentials or paying money, usually by imitating a trusted website or message. The fake site's URL is often one of the few visible clues.

**2. Why did you build this project?**
Answer in your own words. Honest angles that fit this project: it combines ML and defensive security, and it covers the whole path from raw data to a working app rather than only a notebook.

**3. How does PhishGuard work?**
It validates the URL without visiting it, extracts 29 numeric features from the text, feeds them to a trained scikit-learn pipeline, and gets a phishing probability. That is mapped to Legitimate / Suspicious / Potentially Phishing and Low / Medium / High. Separately, simple rules list structural indicators found in the URL.

**4. What features did you extract?**
URL structure (lengths, counts of dots, hyphens, slashes, digits, special characters), hostname traits (subdomain count, IP address, hyphens, digits, punycode), scheme and port, path and query structure (segments, parameters, encoded characters, double slash), the `@` symbol, shortener domains, and a count of suspicious keywords.

**5. Why did you select these features?**
They are cheap to compute from the URL alone, they are commonly discussed in phishing research, and each has a plausible security reason (documented in the README table). I am also clear that each has limitations, so I let the model combine them rather than trusting any single one.

**6. Why Logistic Regression?**
It is a fast, simple baseline and easy to interpret through coefficients. It also shows whether a simple linear model is enough.

**7. Why Random Forest?**
It can capture non-linear interactions between features (for example, "IP address *and* login keyword") and needs no scaling. It is usually strong on tabular features.

**8. Why not deep learning?**
The input is a small table of numeric features, where classical models do well, train in seconds, and are easier to explain. Deep learning (for example on raw URL characters) would need more data and compute and would be harder to interpret. It is a possible future direction.

**9. What is overfitting?**
When a model memorizes training data and performs worse on new data. I compare train and test metrics, use the held-out test set, and limit the Random Forest (`max_depth=20`, `min_samples_leaf=3`).

**10. What is data leakage?**
When information from the test set influences training. I avoid it by fitting the scaler only on training data (inside a `Pipeline`), removing duplicate and conflicting URLs, and splitting by hostname so one website is never in both sets.

**11. What is precision?**
Of the URLs the model calls phishing, the fraction that really are phishing.

**12. What is recall?**
Of all real phishing URLs, the fraction the model caught.

**13. What is F1-score?**
The harmonic mean of precision and recall. It is high only when both are high. I use F1 on the phishing class as my main selection metric.

**14. Why isn't accuracy enough?**
Accuracy counts all correct predictions equally. With imbalanced classes or unequal error costs it can look good while the model misses phishing or raises many false alarms. Precision, recall and the confusion matrix show the trade-off.

**15. What is a false positive?**
A legitimate URL flagged as phishing. It annoys users and makes them distrust the tool.

**16. What is a false negative?**
A phishing URL passed as legitimate. A user could be harmed. Usually the more serious error.

**17. How did you split your dataset?**
80% train and 20% test using `GroupShuffleSplit` grouped by hostname with a fixed random seed (42), so no website appears in both sets. The script prints the class balance of both sets.

**18. How did you handle duplicates?**
Exact duplicate URLs are dropped (first kept). URLs that appear with both labels are removed entirely because the label cannot be trusted. Counts are printed on every run.

**19. How did you handle missing values?**
Rows with a missing URL or label are dropped, and so are invalid labels and URLs that fail validation. The script prints how many were removed at each step. (The dataset's publishers state it has no missing values, and the script still checks.)

**20. How does the prediction pipeline work?**
`analyze_url` in `src/predictor.py`: validate, extract features, build a one-row DataFrame with the same function used in training (`features_to_frame`), call `predict_proba` on the saved pipeline, map the probability to a label and risk level, and add indicators.

**21. How does Flask communicate with the ML model?**
`app.py` only handles HTTP. The `/analyze` route calls `analyze_url()` and returns the dictionary as JSON. The ML logic lives in `src/predictor.py`.

**22. Where is the model stored?**
`models/phishing_model.joblib`. It is a dictionary containing the scikit-learn pipeline, the expected feature names, the model name, test metrics, a timestamp and the scikit-learn version. It is generated locally and not committed.

**23. How is the model loaded?**
With `joblib.load` in `load_model`. It is cached by file modification time, so retraining is picked up without restarting. It checks that the saved feature names match the current code.

**24. What happens if the model is missing?**
A `ModelNotFoundError` with the message "Model file not found. Please train the model first: python src\train_model.py". The API returns HTTP 503, and the page shows a warning banner. Corrupted or outdated model files raise `ModelLoadError` with a retrain message. Users never see a traceback.

**25. What are the limitations?**
URL-only analysis, dataset bias, possible drift over time, unseen attack patterns, small hand-made keyword/shortener/suffix lists, uncalibrated probabilities, and the fact that attackers can adapt.

**26. Can this system guarantee a website is safe?**
No. A low score means the URL structure resembled legitimate URLs in the training data. It does not mean the site is safe, and the page content is never examined.

**27. How could attackers evade a URL-based detector?**
Use a compromised legitimate domain (normal-looking URL), a URL shortener or redirect, a short clean domain with HTTPS, look-alike domains, or hosting on trusted platforms. They can also tweak the URL to avoid features the model relies on (fewer hyphens, no keywords).

**28. How would you improve the project?**
Add domain-age/DNS/reputation features (optional with fallbacks), test on a second dataset to check generalization, calibrate probabilities, add per-prediction explanations, and add robustness tests with obfuscated URLs.

**29. How would you deploy it securely?**
Use a production WSGI server instead of Flask's development server, put it behind HTTPS, keep debug off, add rate limiting, pin dependencies, keep the request size limit, avoid storing user URLs unnecessarily, and only load model files built by my own pipeline (joblib files are pickles).

**30. What did you personally learn from the project?**
Answer from your real experience only. Prompts that may help, if true for you: what surprised you in the "Top features" list, what you learned from train vs test scores, why hostname-grouped splitting matters, or what you fixed while running the tests.

---

## 7. Resume bullets

Use these only after you have run the project. Replace the brackets with **real** numbers from your own training output, or delete the metric.

- Built a Python phishing-URL detection pipeline (29 engineered URL features, scikit-learn) and compared Logistic Regression and Random Forest on the PhiUSIIL dataset (about 235k URLs), reaching [F1 = __ / recall = __] on a hostname-grouped test split.
- Developed a Flask web application that validates submitted URLs and returns a model probability, risk level and rule-based structural indicators without visiting the URL.
- Implemented data cleaning (duplicate and conflicting-label removal), leakage-aware splitting, input validation and automated pytest tests covering features, prediction, preprocessing and API routes.

**GitHub description:**
`Machine-learning based phishing URL detector built with Python, scikit-learn, and Flask.`

---

## 8. Project audit

**Checked by me in a sandbox** (Python 3.12.3, Flask 3.1.3, pandas 3.0.2, NumPy 2.4.4, scikit-learn 1.8.0, joblib 1.5.3):

- Test suite: 74 checks pass, using a small stand-in runner because `pytest` could not be installed there. I also broke the code on purpose and confirmed the tests then failed (5 failures), so they do detect errors.
- `train_model.py` runs end to end (load, inspect, clean, extract, split, train both models, evaluate, select, save) on **synthetic** CSV files with the same `URL`/`label` columns, including a ~235k-row file (about 18 seconds in total there).
- The Flask server starts and its routes respond correctly (page, prediction, invalid input, non-JSON input, static files, security headers). The prediction routes were tried against a throwaway model.
- `script.js` passes a syntax check and behaved correctly against a fake DOM (success, error, no indicators, network failure, and a crafted URL displayed as plain text).
- The throwaway model and metrics files were deleted. **The ZIP contains no trained model and no results.**

**Not checked by me. You must do these:**

| Item | Status |
|---|---|
| Real dataset loads and cleans | to check |
| Training on the real dataset, real metrics | to check |
| `pip install -r requirements.txt` on your machine (Python 3.11+) | to check |
| Real `pytest` run | to check |
| PowerShell / Windows behaviour | to check |
| Page renders correctly in Chrome (layout, focus states, mobile width) | to check |
| README results table filled from your run | to do |
| LICENSE name filled in | to do |
| No secrets committed (`.env` is ignored; none are in the code) | check before pushing |
| You can explain every major file | to do |

Everything is real code with real training and no hard-coded predictions. The only fake data anywhere is the toy URLs in `tests/toy_model.py`, which exist solely so tests can run without the dataset and are labelled as such.
