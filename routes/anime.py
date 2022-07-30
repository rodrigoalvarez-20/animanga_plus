from typing import Optional
from fastapi import APIRouter, Request
from bs4 import BeautifulSoup as bs
from starlette.responses import JSONResponse
import requests

ANIME_BASE_URL = "https://gogoanime.lu"

configs = {
    "gogoanime": {
        "base_url": "https://gogoanime.lu",
        "languages": ["english", "dub-english"],
        "popular_section": {
            "path": "popular.html",
            "params": ["page"],
            "container": {
                "element": "div", 
                "class": "img"
            },
            "title": [
                {
                    "tag": "a", 
                    "class": "",
                    "attribute": "title",
                    "settings": [ { "action": "trim", "status": True } ]
                }
            ],
            "episode_id": [
                {
                    "tag": "a", 
                    "class": "",
                    "attribute": "href", 
                    "settings": [{"action": "split", "separator": "/", "select": -1}]
                }
            ],
            "episode_image": [
                {
                    "tag": "img",
                    "class": "",
                    "attribute": "src"
                }
            ],
            "episode_number": []
        },
        "latest_releases_section": {
            "path": "page-recent-release.html",
            "params": ["page", "type"],
        },
        "anime_details_section": {

        },
        "watch_ep_section": {

        },
        "search_anime_section": {

        }
    },
    "animeflv": {
        "base_url": "https://www3.animeflv.net",
        "languages": ["sub-spanish", "dub-spanish"],
        "popular_section": {

        },
        "latest_releases_section": {

        },
        "anime_details_section": {

        },
        "watch_ep_section": {

        },
        "search_anime_section": {

        }
    }
}


router = APIRouter(prefix="/api/v1/anime")

def dig_tag(root, elements):
    data = None
    for element in elements:
        data = root.find(element["tag"], { "class": element["class"] })[element["attribute"]]
        if data and "settings" in element:
            for setting in element["settings"]:
                if setting["action"] == "trim":
                    data = data.strip()
                elif setting["action"] == "split":
                    data = data.split(setting["separator"])
                    data = data[setting["select"]]
                
    return data


#has_next_req = requests.get(url, params={"page": page + 1})
#has_next = has_next_req.status_code == 200

@router.get("/{page}/popular")
def get_popular_list(page: str, request: Request):
    if page not in configs:
        return JSONResponse({ "error": "El servicio aun no ha sido agregado, por favor intenta con otro" }, 400)
    
    site_config = configs[page]
    base_url = site_config["base_url"]
    popular_config = site_config["popular_section"]
    url = "{}/{}".format(base_url, popular_config["path"])

    query_params = {}
    for param in popular_config["params"]:
        if param in request.query_params._dict:
            query_params[param]: request.query_params.get(param)

    site_res = requests.get(url, params=query_params)
    try:
        site_soup = bs(site_res.text, "html.parser")

        dig_in = popular_config["container"]

        elements_list = site_soup.find_all( dig_in["element"], { "class": dig_in["class"] } )

        if len(elements_list) == 0:
            return JSONResponse({ "error": "No se ha encontrado ningun elemento en la seccion configurada. Por favor cambie el esquema de busqueda" }, 500)

        #TODO: Implementar la busqueda de paginacion
        results = []
        for elem in elements_list:
            episode_title = dig_tag(elem, popular_config["title"])
            episode_id = dig_tag(elem, popular_config["episode_id"])
            episode_image = dig_tag(elem, popular_config["episode_image"])
            episode_number = dig_tag(elem, popular_config["episode_number"])
            results.append({ 
                "link_id": episode_id,
                "title": episode_title,
                "image": episode_image,
                "number": episode_number
            })

        return JSONResponse({"data": results, "total": len(results)}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)

@router.get("/{page}/latest")
def get_latest_releases(page: str, request: Request):
    pass

@router.get("/latest-releases")
def get_latest(page: Optional[int] = 1):
    results = []
    url = "{}/page-recent-release.html".format(ANIME_BASE_URL)
    gogo_res = requests.get(url, params={"page": page, "type": 1})

    if gogo_res.status_code != 200:
        return JSONResponse({"error": "No se ha podido conectar con el servidor"}, gogo_res.status_code)

    try:
        soup = bs(gogo_res.text, 'html.parser')

        recent_added_list = soup.find("ul", {"class": "items"}).find_all("li")

        has_next_req = requests.get(url, params={"page": page + 1})

        has_next = True

        if has_next_req.status_code == 200:
            next_sp = bs(has_next_req.text, 'html.parser')
            has_next = len(next_sp.find(
                "ul", {"class": "items"}).find_all("li")) != 0
        else:
            has_next = False

        for rec in recent_added_list:
            title = rec.find("a")["title"]
            ep_id = rec.find("a")["href"].split("/").pop()
            image = rec.find("img")["src"]
            ep_no = rec.find("p", {"class": "episode"}).getText()
            results.append({"title": title, "id": ep_id,
                           "image": image, "ep_no": ep_no})
        return JSONResponse({"data": results, "has_next": has_next, "total": len(results)}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)


@router.get("/details/{id}")
def anime_info(id: str):
    url = "{}/category/{}".format(ANIME_BASE_URL, id)
    gogo_res = requests.get(url)

    if gogo_res.status_code != 200:
        return JSONResponse({"error": "No se ha podido conectar con el servidor"}, gogo_res.status_code)

    try:
        soup = bs(gogo_res.text, 'html.parser')
        anim_info = soup.find("div", {"class": "anime_info_body_bg"})
        img = anim_info.find("img")["src"]
        name = anim_info.find("h1").getText()
        det = anim_info.find_all("p", {"class": "type"})
        details = {}
        for e in det:
            sp = e.find("span")
            if sp:
                item_name = "_".join(
                    sp.getText().lower().replace(":", "").split())
                if item_name == "type":
                    details[item_name] = e.find("a").getText()
                elif item_name == "plot_summary" or item_name == "released" or item_name == "other_name":
                    details[item_name] = e.getText().split(":", 1)[1].strip()
                elif item_name == "genre":
                    genres = e.find_all("a")
                    details[item_name] = [{"path": x["href"].split(
                        "/").pop(), "title": x["title"]} for x in genres]
                elif item_name == "status":
                    a_tag = e.find("a")
                    path = "{}-anime".format(a_tag.getText().lower())
                    stat = a_tag.getText()
                    details[item_name] = {"link": path, "status": stat}
                else:
                    details[item_name] = ""

        ep_list = soup.find("ul", {"id": "episode_page"}).find_all("li")

        episodes = [{"text": ep.find("a").getText(), "start": int(
            ep.find("a")["ep_start"]), "end": int(ep.find("a")["ep_end"])} for ep in ep_list]

        episodes_link = "{}-episode".format(id)

        return JSONResponse({"image": img, "name": name, **details, "link": episodes_link, "episodes": episodes}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)


@router.get("/watch/{ep_id}")
def watch_episode(ep_id: str):
    url = "{}/{}".format(ANIME_BASE_URL, ep_id)
    gogo_res = requests.get(url)

    if gogo_res.status_code != 200:
        return JSONResponse({"error": "No se ha podido conectar con el servidor"}, gogo_res.status_code)

    try:
        soup = bs(gogo_res.text, 'html.parser')
        ep_data = soup.find("div", {"class": "anime_video_body"})
        if not ep_data:
            return JSONResponse({"error": "No se ha encontrado el contenido solicitado"}, 404)
        ep_title = ep_data.find(
            "h1").getText().replace("at gogoanime", "").strip()
        category = soup.find(
            "div", {"class": "anime_video_body_cate"}).find("a").getText()
        info = soup.find("div", {"class": "anime-info"}).find("a")
        info_link = info["href"].split("/").pop()
        info_title = info.getText()

        prev_info = soup.find(
            "div", {"class": "anime_video_body_episodes_l"}).find("a")
        print(prev_info)
        next_info = soup.find(
            "div", {"class": "anime_video_body_episodes_r"}).find("a")
        prev_video, next_video = None, None
        if prev_info:
            prev_video = {
                "id": prev_info["href"].split("/").pop(),
                "title": prev_info.getText().replace("<<", "").strip()
            }

        if next_info:
            next_video = {
                "id": next_info["href"].split("/").pop(),
                "title": next_info.getText().replace(">>", "").strip()
            }

        providers_data = soup.find(
            "div", {"class": "anime_muti_link"}).find("ul").find_all("li")
        videos = []
        for provider in providers_data:
            link = provider.find("a")["data-video"]
            if link.startswith("//"):
                link = link.replace("//", "https://")
            full_text = provider.find("a").getText()
            provider = full_text.replace(
                "Choose this server", "").replace("\n", "").strip()
            videos.append({"link": link, "provider": provider})

        return JSONResponse({
            "title": ep_title,
            "category": category,
            "info_link": info_link,
            "info_title": info_title,
            "prev": prev_video,
            "next": next_video,
            "videos": videos}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)


@router.get("/search")
def search_anime(query: str, page: Optional[int] = 1):
    url = "{}/search.html".format(ANIME_BASE_URL)
    gogo_res = requests.get(url, {"keyword": query, "page": page})
    if gogo_res.status_code != 200:
        return JSONResponse({"error": "No se ha podido conectar con el servidor"}, gogo_res.status_code)

    try:
        soup = bs(gogo_res.text, 'html.parser')
        paginated_data = soup.find("ul", {"class": "pagination-list"})
        available_pages = 1
        if paginated_data:
            available_pages = len(paginated_data.find_all("li"))

        if page > available_pages:
            return JSONResponse({"error": "El valor de paginación ha excedido el disponible: (max: {})".format(available_pages)}, 400)

        items = soup.find("ul", {"class": "items"}).find_all("li")

        if len(items) == 0:
            return JSONResponse({"error": "No se ha encontrado ningun resultado"}, 404)

        results = []

        for item in items:
            image = item.find("img")["src"]

            name_ref = item.find("p", {"class": "name"}).find("a")
            id_ref = name_ref["href"].split("/").pop()
            name = name_ref.getText().strip()
            released = item.find(
                "p", {"class": "released"}).getText().strip().split()
            if len(released):
                released = released.pop()
            else:
                released = "N/D"

            results.append({
                "image": image,
                "id": id_ref,
                "name": name,
                "year_released": released
            })

        return JSONResponse({"available_pages": available_pages, "results": results}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)
