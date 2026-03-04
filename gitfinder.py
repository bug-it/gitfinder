import sys
import subprocess
import importlib.util

REQUIRED_LIBS = ["flask", "requests", "colorama", "waitress"]

def install_missing_packages():
    print("\n🔎 Verificando dependências...\n")

    for lib in REQUIRED_LIBS:
        if importlib.util.find_spec(lib) is None:
            print(f"🔄 Instalando dependência: {lib} ... ", end="", flush=True)
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", lib],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("✅ SUCESSO")
            except subprocess.CalledProcessError:
                print("❌ FALHA")
        else:
            print(f"✅ {lib} já está instalado")

    print("\n🚀 Verificação concluída.\n")

install_missing_packages()

from flask import Flask, request, jsonify, render_template_string
import requests
import os
import pkgutil
import time
import threading
import webbrowser
import math
import warnings
import logging
from waitress import serve

try:
    from colorama import Fore, init
except:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "colorama"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    from colorama import Fore, init

init(autoreset=True)

warnings.filterwarnings("ignore")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

HOST = "127.0.0.1"
PORT = 5000
GITHUB_API = "https://api.github.com/search/repositories"
GITHUB_TOKEN = "COLE_SEU_TOKEN_AQUI"

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Git Finder PRO</title>

<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&display=swap" rel="stylesheet">

<style>
body{
    margin:0;
    background:#05090f;
    font-family:monospace;
    color:white;
}
.logo{
    font-family: 'Orbitron', sans-serif;
    font-size:110px;
    font-weight:800;
    letter-spacing:6px;
    color:#00ffff;
    text-transform:uppercase;
    text-shadow:
        0 0 5px #00ffff,
        0 0 10px #00ffff,
        0 0 20px #00ffff,
        0 0 40px rgba(0,255,255,0.7);
}
.hero{
    height:100vh;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    text-align:center;
}
.subtitle{
    color:#ff00ff;
    margin-bottom:40px;
    letter-spacing:4px;
}
.search-bar{
    display:flex;
    gap:15px;
    justify-content:center;
}
input{
    padding:14px;
    width:280px;
    background:#0b1622;
    border:1px solid #00ffff;
    border-radius:8px;
    color:white;
    text-align:center;
}
button{
    padding:14px 24px;
    border:none;
    border-radius:8px;
    background:#00ffff;
    cursor:pointer;
    font-weight:bold;
}
.header-fixed{
    display:none;
    position:sticky;
    top:0;
    background:#05090f;
    padding:20px;
    text-align:center;
    border-bottom:1px solid #111;
    z-index:1000;
}
.results-grid{
    display:none;
    padding:30px;
    grid-template-columns:repeat(5,1fr);
    gap:20px;
}
.result{
    position:relative;
    background:linear-gradient(135deg,#0f1c2d,#0c1623);
    border-radius:14px;
    padding:18px;
    height:270px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    overflow:hidden;
    transition:0.3s;
}
.result:hover{
    box-shadow:0 0 15px #00ffff,0 0 30px #00ffff;
    transform:translateY(-5px);
}
.result::before{
    content:"";
    position:absolute;
    left:0;
    top:0;
    width:5px;
    height:100%;
    background:#ff3b3b;
}
.repo-title{
    font-size:14px;
    font-weight:bold;
    text-align:center;
}
.description{
    font-size:12px;
    opacity:.8;
    margin-top:6px;
    height:60px;
    overflow:hidden;
    text-align:center;
}
.stats{
    display:flex;
    justify-content:center;
    gap:25px;
    margin-top:10px;
    font-size:13px;
}
.language-badge{
    display:block;
    padding:5px 10px;
    border-radius:20px;
    font-size:11px;
    margin:8px auto 0 auto;
    width:fit-content;
    color:white;
    font-weight:bold;
}
.links{
    font-size:11px;
    text-align:center;
}
.links a{
    margin:0 8px;
    color:#00ffff;
    text-decoration:none;
    transition:0.3s;
}
.links a:hover{
    color:#ff00ff;
    text-shadow:0 0 10px #ff00ff;
}
.pagination{
    display:none;
    text-align:center;
    padding:20px;
}
.page-number{
    display:inline-block;
    margin:0 6px;
    padding:6px 10px;
    cursor:pointer;
    border-radius:6px;
    background:#111;
}
.page-number:hover{
    background:#00ffff;
    color:black;
}
.loader{
    display:none;
    text-align:center;
    padding:40px;
    font-size:20px;
    color:#00ffff;
    animation:blink 1s infinite alternate;
}
@keyframes blink{
    from{opacity:0.5;}
    to{opacity:1;}
}
.no-results{
    width:100%;
    display:flex;
    justify-content:center;
    align-items:center;
    text-align:center;
    font-size:28px;
    color:#ff00ff;
    text-shadow:0 0 10px #ff00ff;
    padding:80px 0;
}
</style>
</head>
<body>

<div class="hero" id="hero">
    <div class="logo">GIT FINDER</div>
    <div class="subtitle">GITHUB DEEP REPOSITORY FINDER</div>
    <div class="search-bar">
        <input id="query" placeholder="Buscar...">
        <input id="language" placeholder="Linguagem">
        <button onclick="startSearch()">Buscar</button>
    </div>
</div>

<div class="header-fixed" id="headerFixed">
    <div class="logo" style="font-size:60px;">GIT FINDER</div>
    <div class="search-bar" style="margin-top:15px;">
        <input id="queryTop" placeholder="Buscar...">
        <input id="languageTop" placeholder="Linguagem">
        <button onclick="startSearchTop()">Buscar</button>
    </div>
</div>

<div class="loader" id="loader">BUSCANDO...</div>
<div class="results-grid" id="results"></div>
<div class="pagination" id="pagination"></div>

<script>
let currentPage=1;
let totalPages=1;
let lastQuery="";
let lastLanguage="";

function getLanguageColor(lang){
    const colors={
        "JavaScript":"#f1e05a",
        "Python":"#3572A5",
        "Java":"#b07219",
        "C++":"#f34b7d",
        "C":"#555555",
        "Go":"#00ADD8",
        "TypeScript":"#2b7489",
        "PHP":"#4F5D95",
        "Rust":"#dea584",
        "Shell":"#89e051"
    };
    return colors[lang] || "#666";
}

["query","language","queryTop","languageTop"].forEach(id=>{
    document.getElementById(id).addEventListener("keydown",function(e){
        if(e.key==="Enter"){
            e.preventDefault();
            if(id.includes("Top")) startSearchTop();
            else startSearch();
        }
    });
});

function startSearch(){
    if(query.value.trim()==="" && language.value.trim()==="") return;
    lastQuery=query.value;
    lastLanguage=language.value;
    currentPage=1;
    activateResults();
    fetchResults();
}

function startSearchTop(){
    if(queryTop.value.trim()==="" && languageTop.value.trim()==="") return;
    lastQuery=queryTop.value;
    lastLanguage=languageTop.value;
    currentPage=1;
    fetchResults();
}

function activateResults(){
    hero.style.display="none";
    headerFixed.style.display="block";
    results.style.display="grid";
    pagination.style.display="block";
    queryTop.value=lastQuery;
    languageTop.value=lastLanguage;
}

function fetchResults(){
    loader.style.display="block";
    results.innerHTML="";
    pagination.innerHTML="";

    fetch("/search",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({query:lastQuery,language:lastLanguage,page:currentPage})
    })
    .then(res=>res.json())
    .then(data=>{
        loader.style.display="none";
        totalPages=data.total_pages;

        if(data.results.length===0){
            results.innerHTML="<div class='no-results'>NENHUM REPOSITÓRIO ENCONTRADO</div>";
            return;
        }

        data.results.forEach(repo=>{
            let color=getLanguageColor(repo.language);
            results.innerHTML+=`
            <div class="result">
                <div>
                    <div class="repo-title">${repo.name}</div>
                    <div class="description">${repo.description}</div>
                    <div class="stats">
                        <div>⭐ ${repo.stars}</div>
                        <div>🍴 ${repo.forks}</div>
                        <div>📦 ${repo.size}</div>
                    </div>
                    <div class="language-badge" style="background:${color}">
                        ${repo.language}
                    </div>
                </div>
                <div class="links">
                    <a href="${repo.url}" target="_blank">🗂️ REPO</a>
                    <a href="${repo.git_url}" target="_blank">🔗 GIT</a>
                    <a href="${repo.zip_url}" target="_blank">🗄️ ZIP</a>
                </div>
            </div>`;
        });

        renderPagination();
    });
}

function renderPagination(){
    for(let i=1;i<=totalPages;i++){
        pagination.innerHTML+=
        `<span class="page-number" onclick="goToPage(${i})">${i}</span>`;
    }
}

function goToPage(page){
    currentPage=page;
    fetchResults();
}
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query", "")
    language = data.get("language", "")
    page = int(data.get("page", 1))

    if not query and not language:
        return jsonify({"results": [], "total_pages": 1})

    if query and language:
        search_query = f"{query} in:name,description language:{language}"
    elif language:
        search_query = f"language:{language}"
    else:
        search_query = query

    per_page = 100

    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
        "page": page
    }

    headers = {}
    if GITHUB_TOKEN != "COLE_SEU_TOKEN_AQUI":
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        r = requests.get(GITHUB_API, params=params, headers=headers, timeout=15)
        data_json = r.json()
    except Exception:
        return jsonify({"results": [], "total_pages": 1})

    total_count = min(data_json.get("total_count", 0), 1000)
    total_pages = max(1, math.ceil(total_count/per_page))

    results = []
    for repo in data_json.get("items", []):
        desc = repo.get("description") or ""
        desc = desc[:140] + ("..." if len(desc) > 140 else "")
        size_mb = round(repo.get("size", 0)/1024, 2)
        default_branch = repo.get("default_branch", "main")

        results.append({
            "name": repo.get("full_name", ""),
            "description": desc,
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "size": f"{size_mb} MB",
            "language": repo.get("language") or "Unknown",
            "url": repo.get("html_url", ""),
            "git_url": repo.get("html_url", "")+".git",
            "zip_url": f"{repo.get('html_url','')}/archive/refs/heads/{default_branch}.zip"
        })

    return jsonify({"results": results, "total_pages": total_pages})

def open_browser():
    time.sleep(1)
    webbrowser.open(f"http://{HOST}:{PORT}")

threading.Thread(target=open_browser, daemon=True).start()

print("\n🚀 Git Finder iniciado com sucesso!")
print("🌐 Aplicação rodando em produção (Waitress).")
print("✨ Tudo pronto para uso.\n")

serve(app, host=HOST, port=PORT)
