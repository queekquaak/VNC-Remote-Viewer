import requests
from modules import config
from flask import Flask, render_template, jsonify, request

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

API_BASE = f"http://{config.API_SERVER_ADDR}"


@app.route('/')
def index():
    cfg = config.to_dict()
    return render_template('index.html', config=cfg)


@app.route('/api/servers', methods=['GET'])
def get_servers():
    try:
        params = {
            'include_excluded': request.args.get('include_excluded') == 'true',
            'light': request.args.get('light') == 'true',
            'quality': 'low' if request.args.get('tile_mode') else 'medium'
        }
        resp = requests.get(f"{API_BASE}/api/servers", params=params)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/servers/exclude', methods=['POST'])
def exclude_server():
    try:
        resp = requests.post(f"{API_BASE}/api/servers/exclude", json=request.json)
        return jsonify(resp.json() if resp.content else {"status": "ok"}), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/servers/include', methods=['POST'])
def include_server():
    try:
        resp = requests.post(f"{API_BASE}/api/servers/include", json=request.json)
        return jsonify(resp.json() if resp.content else {"status": "ok"}), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/servers/check', methods=['GET'])
def check_server():
    try:
        ip = request.args.get('ip')
        ws_port = request.args.get('websockify_port')
        resp = requests.get(f"{API_BASE}/api/servers/check", params={'ip': ip, 'port': ws_port})
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lists', methods=['GET'])
def get_lists():
    try:
        lists = config.load_lists()
        return jsonify(lists), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.after_request
def add_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.after_request
def add_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, max-age=0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.route('/api/lists', methods=['GET', 'POST'])
def handle_lists():
    if request.method == 'GET':
        try:
            lists = config.load_lists()
            return jsonify(lists), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    try:
        data = request.json
        action = data.get('action')
        list_name = data.get('list_name')
        servers = data.get('servers', [])

        lists = config.load_lists()

        if action == 'add':
            if list_name not in lists:
                lists[list_name] = []
            # Добавляем только отсутствующие серверы
            for server in servers:
                if server not in lists[list_name]:
                    lists[list_name].append(server)
        elif action == 'remove':
            if list_name in lists:
                if servers:
                    # Удаляем только присутствующие серверы
                    lists[list_name] = [s for s in lists[list_name] if s not in servers]
                else:
                    # Удаляем весь список
                    del lists[list_name]

        config.save_lists(lists)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(config.FRONTEND_PORT)
    app.run(host='0.0.0.0', port=port, debug=False)
