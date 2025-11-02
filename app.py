#!/usr/bin/env python3
from flask import Flask, request, send_file, render_template_string, jsonify, redirect, url_for
import tempfile
import os
import datetime
import uuid
from aged_care_calcs import agedcare_sim

app = Flask(__name__)
history = []

# --- Modern Dark Theme HTML ---
HTML_INDEX = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Aged Care Financial Simulator</title>
  <style>
    :root {
      --bg: #121212;
      --card-bg: #1E1E1E;
      --accent: #00bfa6;
      --text: #EAEAEA;
      --muted: #9e9e9e;
      --border: #2c2c2c;
      --danger: #ff7675;
      --font: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      margin: 0;
      padding: 2em;
      display: flex;
      justify-content: center;
    }
    .container {
      width: 100%;
      max-width: 1000px;
    }
    h1, h2 {
      color: var(--accent);
      margin-top: 0.5em;
      font-weight: 600;
    }
    form {
      background: var(--card-bg);
      padding: 1.5em 2em;
      border-radius: 1rem;
      box-shadow: 0 0 12px rgba(0,0,0,0.6);
    }
    label {
      display: block;
      margin-top: 0.8em;
      color: var(--muted);
      font-size: 0.95em;
    }
    input {
      width: 100%;
      background: #2c2c2c;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px;
      border-radius: 0.4rem;
      margin-top: 4px;
      font-size: 1em;
    }
    input:focus {
      outline: none;
      border-color: var(--accent);
      background: #333;
    }
    button {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0.7em 1.4em;
      border-radius: 0.5rem;
      margin-top: 1.5em;
      font-size: 1em;
      cursor: pointer;
      transition: 0.2s ease;
    }
    button:hover {
      background: #00d9b9;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin-top: 2em;
      background: var(--card-bg);
      border-radius: 1rem;
      overflow: hidden;
      box-shadow: 0 0 10px rgba(0,0,0,0.6);
    }
    th, td {
      padding: 10px 14px;
      text-align: left;
    }
    th {
      background: #272727;
      color: var(--accent);
      font-weight: 600;
      font-size: 0.9em;
    }
    tr:nth-child(even) { background-color: #181818; }
    tr:nth-child(odd) { background-color: #1f1f1f; }
    a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 500;
    }
    a:hover {
      text-decoration: underline;
    }
    .muted {
      color: var(--muted);
      font-style: italic;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Aged Care Financial Simulator</h1>

    <form action="/simulate" method="post">
      {% for field, default in fields.items() %}
        <label>{{ field.replace('-', ' ').title() }}
          <input name="{{ field }}" value="{{ default }}" required>
        </label>
      {% endfor %}
      <label>Output filename (without extension):
        <input name="output_filename" value="agedcare_sim_result">
      </label>
      <button type="submit">Run Simulation</button>
    </form>

    <h2>Download History</h2>
    {% if history %}
      <table>
        <tr>
          <th>Time</th>
          <th>Initial Assets</th>
          <th>RAD</th>
          <th>House Value</th>
          <th>Downloads</th>
        </tr>
        {% for item in history %}
          <tr>
            <td>{{ item.timestamp }}</td>
            <td>{{ item.params['initial-assets'] }}</td>
            <td>{{ item.params['rad'] }}</td>
            <td>{{ item.params['house-value'] }}</td>
            <td>
              <a href="/download/{{ item.id }}?type=csv">CSV</a> |
              <a href="/download/{{ item.id }}?type=excel">Excel</a>
            </td>
          </tr>
        {% endfor %}
      </table>
    {% else %}
      <p class="muted">No simulations run yet.</p>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    defaults = {
        "initial-assets": 140000,
        "rad": 750000,
        "house-value": 1000000,
        "dap-percentage": 7,
        "income-interest-rate": 4,
        "start-date": datetime.date.today().isoformat(),
        "months-till-house-sale": 6,
        "total-months-after-sale": 120,
        "basic-daily-fee": 63.82,
        "means-tested-fee": 25,
        "means-tested-lifetime-limit": 82347,
        "special-services-fee": 70,
        "pension-initial": 2200,
        "pension-final": 2200,
        "incidental-expenditure-mthly": 400,
        "asset-interest-percentage": 70,
    }
    return render_template_string(HTML_INDEX, fields=defaults, history=reversed(history))

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        params = {k: request.form[k] for k in request.form if k != 'output_filename'}
        base_filename = request.form.get('output_filename', '').strip() or "agedcare_sim_result"

        args = {k.replace('-', '_'): v for k, v in params.items()}
        float_fields = [
            'initial_assets', 'rad', 'house_value', 'dap_percentage', 'income_interest_rate',
            'basic_daily_fee', 'means_tested_fee', 'means_tested_lifetime_limit',
            'special_services_fee', 'pension_initial', 'pension_final',
            'incidental_expenditure_mthly', 'asset_interest_percentage'
        ]
        int_fields = ['months_till_house_sale', 'total_months_after_sale']
        date_fields = ['start_date']

        for f in float_fields:
            args[f] = float(args[f])
        for f in int_fields:
            args[f] = int(args[f])
        for f in date_fields:
            args[f] = datetime.datetime.strptime(args[f], "%Y-%m-%d").date()

        results = agedcare_sim.simulate_finances(**args)

        tmpdir = tempfile.mkdtemp()
        csv_path = os.path.join(tmpdir, f"{base_filename}.csv")
        excel_path = os.path.join(tmpdir, f"{base_filename}.xlsx")

        agedcare_sim.save_csv(csv_path, results)
        agedcare_sim.save_excel(excel_path, results)

        item_id = str(uuid.uuid4())
        history.append({
            "id": item_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params": params,
            "files": {"csv": csv_path, "excel": excel_path}
        })

        return redirect(url_for('index'))

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/download/<item_id>')
def download(item_id):
    file_type = request.args.get("type")
    if file_type not in ["csv", "excel"]:
        return jsonify({"error": "Invalid type"}), 400

    for item in history:
        if item["id"] == item_id:
            file_path = item["files"][file_type]
            if file_path and os.path.exists(file_path):
                mime = "text/csv" if file_type == "csv" else \
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                return send_file(file_path, mimetype=mime, as_attachment=True,
                                 download_name=os.path.basename(file_path))
            return jsonify({"error": "File not found"}), 404

    return jsonify({"error": "Item not found"}), 404


if __name__ == "__main__":
    app.run(host"0.0.0.0",debug=True, port=5000)
