import os

from flask import Flask, render_template, jsonify, request
from transformers import BertModel, AutoTokenizer

from glance import glance
from sg import query_highlighted_file_line_range, parse_url


app = Flask(__name__)

model_path = os.environ["GLANCE_MODEL_PATH"]
model = BertModel.from_pretrained(model_path).eval()
tokenizer = AutoTokenizer.from_pretrained(model_path)
cache = {}


@app.route("/glance")
def glance_view():
    url = request.args.get("file")
    if not url:
        return "Missing file parameter", 400

    repo_name, commit_id, file_path = parse_url(url)

    if url in cache:
        return jsonify(cache[url])

    content, highlighted_content = query_highlighted_file_line_range(
        repo_name,
        commit_id,
        file_path,
        0,
        2**31 - 1,
    )

    line_windows = glance(model, tokenizer, content, 10)
    response = {"lineWindows": line_windows, "highlightedContent": highlighted_content}
    cache[url] = response

    return jsonify(response)


@app.route("/")
def index():
    url = request.args.get("file")
    if not url:
        return "Missing file parameter", 400

    return render_template("index.html")
