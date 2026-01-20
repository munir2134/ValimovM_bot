# run_all.py
import os
import sys
import math
import json
import random
import pandas as pd
import webview
import numpy as np

# Попытка импортировать KDTree из sklearn
try:
    from sklearn.neighbors import KDTree
except Exception as e:
    print("Ошибка: требуется scikit-learn. Установите: pip install scikit-learn")
    raise

# -----------------------------
# Настройки проекта (меняйте)
# -----------------------------
project_dir = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(project_dir, "abonenty.xlsx")
html_file = os.path.join(project_dir, "map.html")
bs_json_file = os.path.join(project_dir, "bs_results.json")

LAT_MIN, LAT_MAX = 41.15, 41.35
LON_MIN, LON_MAX = 69.05, 69.45
NUM_SUBSCRIBERS = 1000

R_km = 3.0
capacity = 150

# -----------------------------
# 1. Генерация базы абонентов
# -----------------------------
random.seed(42)
subscribers = [
    {
        "ID": i + 1,
        "Name": f"Абонент {i + 1}",
        "Phone": "+9989" + str(random.randint(10000000, 99999999)),
        "Email": f"user{i+1}@example.com",
        "Lat": round(random.uniform(LAT_MIN, LAT_MAX), 6),
        "Lon": round(random.uniform(LON_MIN, LON_MAX), 6),
    }
    for i in range(NUM_SUBSCRIBERS)
]

# -----------------------------
# 2. Сохраняем Excel
# -----------------------------
df = pd.DataFrame(subscribers)
df.to_excel(excel_file, index=False)
print(f"✔️ Excel создан: {excel_file}")

# -----------------------------
# 3. Функция проекции lat/lon -> км
# -----------------------------
def latlon_to_xy_km_array(lats, lons, lat0=None, lon0=None):
    if lat0 is None:
        lat0 = float(np.mean(lats))
    if lon0 is None:
        lon0 = float(np.mean(lons))
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat0))
    xs = (lons - lon0) * km_per_deg_lon
    ys = (lats - lat0) * km_per_deg_lat
    return xs, ys, lat0, lon0

# -----------------------------
# 4. Размещение БС
# -----------------------------
def place_base_stations(subscribers, R_km=3.0, capacity=150):
    N = len(subscribers)
    lats = np.array([u["Lat"] for u in subscribers], dtype=float)
    lons = np.array([u["Lon"] for u in subscribers], dtype=float)
    xs, ys, lat0, lon0 = latlon_to_xy_km_array(lats, lons)
    pts = np.vstack([xs, ys]).T
    tree = KDTree(pts, leaf_size=40)

    unassigned = set(range(N))
    assignment = [-1] * N
    bs_list = []

    while unassigned:
        candidates = list(unassigned)
        neighs = tree.query_radius(pts[candidates], r=R_km)
        best_cover = -1
        best_candidate_idx = None
        best_neigh_list = None

        for i_cand, neigh in enumerate(neighs):
            neigh_unassigned = [n for n in neigh if n in unassigned]
            if len(neigh_unassigned) > best_cover:
                best_cover = len(neigh_unassigned)
                best_candidate_idx = candidates[i_cand]
                best_neigh_list = neigh_unassigned

        if best_cover <= 0:
            idx = unassigned.pop()
            bs_assigned = [idx]
            bs_x = xs[idx]; bs_y = ys[idx]
            bs_lat = float(subscribers[idx]["Lat"])
            bs_lon = float(subscribers[idx]["Lon"])
        else:
            center = pts[best_candidate_idx]
            neigh_points = pts[best_neigh_list]
            dists = np.linalg.norm(neigh_points - center, axis=1)
            order = np.argsort(dists)
            take = order[:capacity]
            bs_assigned = [best_neigh_list[i] for i in take]
            bs_x = float(xs[best_candidate_idx])
            bs_y = float(ys[best_candidate_idx])
            bs_lat = float(subscribers[best_candidate_idx]["Lat"])
            bs_lon = float(subscribers[best_candidate_idx]["Lon"])
            for idx in bs_assigned:
                unassigned.discard(idx)

        bs_index = len(bs_list)
        for idx in bs_assigned:
            assignment[idx] = bs_index

        bs_list.append({
            "id": bs_index,
            "x_km": float(bs_x),
            "y_km": float(bs_y),
            "Lat": float(bs_lat),
            "Lon": float(bs_lon),
            "assigned_indices": bs_assigned
        })

    return {
        "params": {"R_km": R_km, "capacity": capacity, "N": N, "num_bs": len(bs_list), "lat0": lat0, "lon0": lon0},
        "bs": [{"id": b["id"], "Lat": b["Lat"], "Lon": b["Lon"], "load": len(b["assigned_indices"])} for b in bs_list],
        "assignment": [
            {"subscriber_index": i, "ID": subscribers[i]["ID"], "Lat": subscribers[i]["Lat"], "Lon": subscribers[i]["Lon"], "bs_id": assignment[i]}
            for i in range(N)
        ]
    }

print("Запускаю размещение базовых станций...")
bs_results = place_base_stations(subscribers, R_km=R_km, capacity=capacity)
with open(bs_json_file, "w", encoding="utf-8") as f:
    json.dump(bs_results, f, ensure_ascii=False, indent=2)
print(f"✔️ Результаты размещения сохранены: {bs_json_file}")
print(f"Найдено базовых станций: {len(bs_results['bs'])} (нижняя граница ceil(N/capacity) = {math.ceil(len(subscribers)/capacity)})")

# -----------------------------
# 5. Генерация HTML
# -----------------------------
subs_json = json.dumps(subscribers, ensure_ascii=False)
bs_json = json.dumps(bs_results, ensure_ascii=False)

html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
<title>Абоненты + БС</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<style>
body {{ margin:0; font-family: Arial, sans-serif; display:flex; height:100vh; }}
#sidebar {{ width:320px; background:#1e1e1e; color:#fff; padding:18px; overflow-y:auto; }}
#map {{ flex:1; }}
input, button, select {{ width:95%; padding:8px; margin-bottom:10px; border-radius:6px; border:none; }}
button {{ background:#0d6efd; color:#fff; cursor:pointer; }}
button:hover {{ background:#0b5ed7; }}
#infoButton {{ position:absolute; top:10px; right:10px; width:auto; padding:5px 10px; background:#28a745; }}
#phoneDisplay {{ margin-top:10px; padding:8px; background:#333; color:#fff; border-radius:6px; }}
.legend-item {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; }}
.color-box {{ width:18px; height:18px; border-radius:4px; display:inline-block; }}
</style>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
</head>
<body>
<div id="sidebar">
  <h2>🔍 Поиск абонента</h2>
  <input id="search" placeholder="Введите ID или номер">
  <button onclick="searchUser()">Найти</button>
  <button id="infoButton" onclick="openExcel()">Информация (Excel)</button>
  <div id="phoneDisplay"></div>

  <h3>Параметры БС</h3>
  <div>Радиус (км): <b id="paramR">{R_km}</b></div>
  <div>Емкость: <b id="paramC">{capacity}</b></div>
  <div>Найдено БС: <b id="paramNum">{len(bs_results['bs'])}</b></div>

  <h3>Легенда</h3>
  <div id="legend"></div>
  <hr/>
  <div><small>Сгенерировано: {NUM_SUBSCRIBERS} абонентов</small></div>
</div>

<div id="map"></div>

<script>
var users = {subs_json};
var bs_results = {bs_json};
var map = L.map('map').setView([41.2995,69.2401],12);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);

var colors = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6","#bcf60c","#fabebe",
              "#008080","#800000","#aaffc3","#808000","#ffd8b1","#000075","#808080","#ffffff","#000000","#696969"];

function colorFor(id) {{
    return colors[id % colors.length];
}}

// Легенда (первые 10 БС)
var legendDiv = document.getElementById('legend');
bs_results.bs.slice(0, 10).forEach(function(b) {{
    var item = document.createElement('div');
    item.className = 'legend-item';
    var box = document.createElement('span');
    box.className = 'color-box';
    box.style.background = colorFor(b.id);
    item.appendChild(box);
    var txt = document.createElement('span');
    txt.innerText = 'BS ' + b.id + ' (load: ' + b.load + ')';
    item.appendChild(txt);
    legendDiv.appendChild(item);
}});

// Маркеры абонентов
var assignmentByID = {{}};
bs_results.assignment.forEach(function(a) {{ assignmentByID[a.ID] = a.bs_id; }});
var markers = [];
users.forEach(function(u, idx) {{
    var bsid = assignmentByID[u.ID];
    var circle = L.circleMarker([u.Lat, u.Lon], {{
        radius: 5,
        fillOpacity: 0.9,
        color: (bsid === -1 ? '#888' : colorFor(bsid)),
        weight: 1
    }}).addTo(map).bindPopup(u.Name + "<br>" + u.Phone + "<br>BS: " + bsid);
    markers.push(circle);
}});

// Зоны покрытия и клик на БС
var R_m = bs_results.params.R_km * 1000;
bs_results.bs.forEach(function(b) {{
    var coverageCircle = L.circle([b.Lat, b.Lon], {{ radius: R_m, color: colorFor(b.id), fillOpacity: 0.08 }}).addTo(map);
    coverageCircle.on('click', function() {{
        map.setView([b.Lat, b.Lon], 14); // центрируем и увеличиваем зум
    }});
    L.marker([b.Lat, b.Lon]).addTo(map).bindPopup("BS " + b.id + "<br>load: " + b.load);
}});

// Поиск абонента
function resetMarkers() {{
    markers.forEach(m => m.setStyle({{radius:5}}));
}}

function searchUser() {{
    var q = document.getElementById("search").value.trim();
    var numQ = Number(q);
    var found = users.filter(u => ((!isNaN(numQ) && u.ID === numQ) || u.Phone === q));
    if(found.length > 0) {{
        var user = found[0];
        map.setView([user.Lat, user.Lon],15);
        resetMarkers();
        var idx = users.findIndex(u => u.ID === user.ID);
        if(idx >= 0) {{
            markers[idx].setStyle({{radius:9}});
            markers[idx].openPopup();
        }}
        document.getElementById("phoneDisplay").innerHTML = "Телефон: " + user.Phone + "<br>Email: " + user.Email + "<br>BS: " + assignmentByID[user.ID];
    }} else {{
        alert("Абонент не найден!");
        document.getElementById("phoneDisplay").innerHTML = "";
        resetMarkers();
    }}
}}

document.getElementById("search").addEventListener("keypress", function(e) {{
    if(e.key === "Enter") searchUser();
}});

function openExcel() {{
    if(window.pywebview && window.pywebview.api && window.pywebview.api.open_excel) {{
        window.pywebview.api.open_excel();
    }} else {{
        alert("Open Excel: API недоступен (если карта открыта не через приложение).");
    }}
}}
</script>
</body>
</html>
"""

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"✔️ HTML с картой создан: {html_file}")

# -----------------------------
# 6. Класс API для PyWebView
# -----------------------------
class API:
    def open_excel(self):
        try:
            if os.name == "nt":
                os.startfile(excel_file)
            elif sys.platform == "darwin":
                os.system(f"open '{excel_file}'")
            else:
                os.system(f"xdg-open '{excel_file}'")
        except Exception as e:
            print("Не удалось открыть Excel:", e)

# -----------------------------
# 7. Запуск PyWebView
# -----------------------------
api = API()
window = webview.create_window("Абоненты + БС", html_file, width=1200, height=800, js_api=api)
webview.start()









