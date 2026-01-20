
var map = L.map('map').setView([41.2995,69.2401],12);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{ maxZoom:19 }).addTo(map);

var users = [];

fetch('abonenty.json')
.then(response => response.json())
.then(data => {
    users = data;
    // добавляем все маркеры
    users.forEach(u => {
        L.marker([u.Lat,u.Lon])
            .bindPopup("<b>"+u.Name+"</b><br>"+u.Phone+"<br>Последний раз в сети: "+u.LastSeen)
            .bindTooltip(u.Name+" | "+u.Phone)
            .addTo(map);
    });
});

function searchUser(){
    var q = document.getElementById("search").value.trim();
    var box = document.getElementById("results");
    box.innerHTML = "";
    var numQ = Number(q);
    var found = users.filter(u => (!isNaN(numQ) && u.ID === numQ) || u.Phone === q);
    if(found.length===0){box.innerHTML="<p>Ничего не найдено</p>"; return;}
    map.eachLayer(layer => { if(layer instanceof L.Marker) map.removeLayer(layer); });
    found.forEach(u => {
        var marker = L.marker([u.Lat,u.Lon])
            .bindPopup("<b>"+u.Name+"</b><br>"+u.Phone+"<br>Последний раз в сети: "+u.LastSeen)
            .bindTooltip(u.Name+" | "+u.Phone)
            .addTo(map);
        map.setView([u.Lat,u.Lon],15);
        var div = document.createElement("div");
        div.className = "user";
        div.innerHTML = "<b>"+u.Name+"</b><br>"+u.Phone;
        div.onclick = function(){ map.setView([u.Lat,u.Lon],15); marker.openPopup(); };
        box.appendChild(div);
    });
}
