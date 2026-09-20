"""PhishGuard web app. Start with:  python app.py  then open http://127.0.0.1:5000

This file only handles web requests. All ML logic lives in src/predictor.py.
"""

import logging

from flask import Flask, jsonify, render_template, request

from src.predictor import analyze_url, model_file_exists
from src.utils import InvalidURLError, ModelLoadError, ModelNotFoundError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # a URL request should be tiny

logger = logging.getLogger("phishguard")


def error_response(message, status):
    return jsonify(ok=False, error=message), status


@app.get("/")
def index():
    return render_template("index.html", model_ready=model_file_exists())


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "url" not in data:
        return error_response('Send JSON such as {"url": "https://example.com"}.', 400)

    try:
        result = analyze_url(data["url"])
    except InvalidURLError as exc:
        return error_response(str(exc), 400)
    except (ModelNotFoundError, ModelLoadError) as exc:
        return error_response(str(exc), 503)
    except Exception:
        # Full details go to the server log; the user only sees a generic message.
        logger.exception("Unexpected error while analyzing a URL")
        return error_response("Something went wrong while analyzing this URL. Please try again.", 500)

    return jsonify(ok=True, result=result)


@app.errorhandler(413)
def too_large(_error):
    return error_response("The request is too large.", 413)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    # The page loads only its own CSS and JS, so everything else can be blocked.
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


if __name__ == "__main__":
    # 127.0.0.1 = reachable only from this computer. debug is off on purpose:
    # Flask's debug mode exposes an interactive debugger.
    app.run(host="127.0.0.1", port=5000, debug=False)
