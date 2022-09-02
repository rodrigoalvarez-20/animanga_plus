from typing import Optional
from fastapi import APIRouter, Request
from bs4 import BeautifulSoup as bs
from starlette.responses import JSONResponse
import requests
import js2py
from requests_html import HTMLSession, AsyncHTMLSession

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
                    "settings": [{"action": "trim", "status": True}]
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
            "container": {
                "element": "ul",
                "class": "items",
                "children": {
                    "tag": "li",
                    "class": ""
                }
            },
            "title": [
                {
                    "tag": "a",
                    "class": "",
                    "attribute": "title",
                    "settings": [{"action": "trim", "status": True}]
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
            "episode_number": [
                {
                    "tag": "p",
                    "class": "episode",
                    "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
                }
            ]
        },
        "anime_details_section": {
            "path": "category",
            "params": [],
            "image": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag":"img",
                "class": "",
                "attribute": "src"
            },
            "title": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag": "h1",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "type": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    },
                    {
                        "tag": "p",
                        "class": "type",
                        "index": 0,
                    }
                ],
                "tag": "a",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "summary": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag": "p",
                "class": "type",
                "index": 1,
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": ",",
                        "with": ""
                    },
                    {
                        "action": "replace",
                        "source": "Plot Summary:",
                        "with": ""
                    },
                    {
                        "action": "replace",
                        "source": "\r\n",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "genre": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    },
                    {
                        "tag": "p",
                        "class": "type",
                        "index": 2,
                    }
                ],
                "type": "list",
                "tag": "a",
                "class": "",
                "settings": [
                    {
                        "action": "getText"
                    }, 
                    {
                        "action": "replace", 
                        "source": ",", 
                        "with": ""
                    }, 
                    {
                        "action": "trim", 
                        "status": True
                    }
                ]
            },
            "other_names": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag": "p",
                "class": "type",
                "index": 5,
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": "Other name:",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "status": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag": "p",
                "class": "type",
                "index": 4,
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": "Status: \n",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "released_date": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "anime_info_body_bg"
                    }
                ],
                "tag": "p",
                "class": "type",
                "index": 3,
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": "Released:",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "episodes": {
                "type": "paginated",
                "containers": [
                    {
                        "tag": "ul",
                        "id": "episode_page"
                    }
                ],
                "list_container": {
                    "tag": "li",
                    "class": ""
                },
                "title": "EP {number}",
                "link": "{id}-episode-{number}",
                "start": {
                    "tag": "a",
                    "attribute": "ep_start"
                },
                "end": {
                    "tag": "a",
                    "attribute": "ep_end"
                }
            }
        },
        "watch_ep_section": {

        },
        "search_anime_section": {

        }
    },
    "animeflv": {
        "base_url": "https://www.animeflv.one",
        "languages": ["sub-spanish", "dub-spanish"],
        "latest_releases_section": {
            "path": "/",
            "container": {
                "element": "div",
                "class": "ul hm",
                "children": {
                    "tag": "article",
                    "class": "li"
                }
            },
            "title": [
                {
                    "tag": "span",
                    "class": "",
                    "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
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
                    "attribute": "data-src"
                }
            ],
            "episode_number": [
                {
                    "tag": "u",
                    "class": "",
                    "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
                }
            ]
        },
        "anime_details_section": {
            "path": "anime",
            "params": [],
            "image": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "ll",
                        "id": "l"
                    },
                    {
                        "tag": "div",
                        "class": "info-l"
                    },
                    {
                        "tag": "figure",
                        "class": "i"
                    }
                ],
                "tag": "img",
                "class": "",
                "attribute": "data-src"
            },
            "title": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "info-t"
                    },
                    {
                        "tag": "div",
                        "class": "cn"
                    },
                    {
                        "tag": "div",
                        "class": "ti"
                    },
                    {
                        "tag": "div",
                        "class": ""
                    },
                    {
                        "tag": "h2",
                        "class": ""
                    }
                ],
                "tag": "i",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "summary": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "info-r"
                    },
                    {
                        "tag": "div",
                        "class": "tx"
                    }
                ],
                "tag": "p",
                "class": "",
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": "\"",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "genre": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "info-r"
                    },
                    {
                        "tag": "ul",
                        "class": "gn"
                    }
                ],
                "type": "list",
                "tag": "a",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "other_names": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "info-t"
                    },
                    {
                        "tag": "div",
                        "class": "cn"
                    },
                    {
                        "tag": "div",
                        "class": "ti"
                    },
                    {
                        "tag": "ul",
                        "class": ""
                    }
                ],
                "type": "list",
                "tag": "li",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "status": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "st c-e"
                    }
                ],
                "tag": "span",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "rating": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "rnk"
                    }
                ],
                "tag": "div",
                "class": "ra",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "episodes": {
                "type": "dynamic",
                "containers": [
                    {
                        "tag": "section",
                        "class": "cn",
                    },
                    {
                        "tag": "div",
                        "class": "rr",
                        "id": "r"
                    },
                    {
                        "tag": "div",
                        "class": "info-r episodes"
                    }
                ],
                "tag": "script",
                "class": "",
                "id": "",
                "image_template": "{base_url}/cdn/episodes/"
            }
        },
        "watch_ep_section": {

        },
        "search_anime_section": {

        }
    },
    "animeninja": {
        "base_url": "https://www1.animeonline.ninja",
        "languages": ["sub-spanish", "dub-spanish", "japanese"],
        "latest_releases_section": {
            "path": "episodio",
            "container": {
                "element": "div",
                "class": "animation-2 items",
                "children": {
                    "tag": "article",
                    "class": "episodes"
                }
            },
            "title": [
                {
                    "tag": "center",
                    "class": ""
                },
                {
                    "tag": "div",
                    "class": "data"
                },
                {
                    "tag": "h3",
                    "class": "",
                    "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
                }
            ],
            "episode_id": [
                {
                    "tag": "div",
                    "class": "poster"
                },
                {
                    "tag": "div",
                    "class": "season_m animation-1"
                },
                {
                    "tag": "a",
                    "class": "",
                    "attribute": "href",
                    "settings": [{"action": "split", "separator": "/", "select": -2}]
                }
            ],
            "episode_image": [
                {
                    "tag": "div",
                    "class": "poster"
                },
                {
                    "tag": "img",
                    "class": "lazy",
                    "attribute": "data-src"
                }
            ],
            "episode_number": [
                {
                    "tag": "h4",
                    "class": "",
                    "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
                }
            ]
        },
        "anime_details_section": {
            "path": "online",
            "params": [],
            "image": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sheader"
                    },
                    {
                        "tag": "div",
                        "class": "poster"
                    }
                ],
                "tag": "img",
                "class": "lazy",
                "attribute": "data-src"
            },
            "title": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sheader"
                    },
                    {
                        "tag": "div",
                        "class": "data"
                    }
                ],
                "tag": "h1",
                "class": "",
                "settings": [{"action": "getText"}, {"action": "trim", "status": True}]
            },
            "summary": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sbox fixidtab",
                        "id": "info"
                    },
                    {
                        "tag": "div",
                        "class": "wp-content"
                    }
                ],
                "tag": "p",
                "class": "",
                "index": 0,
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "replace",
                        "source": "\"",
                        "with": ""
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "genre": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sheader"
                    },
                    {
                        "tag": "div",
                        "class": "data"
                    },
                    {
                        "tag": "div",
                        "class": "sgeneros"
                    }
                ],
                "type": "list",
                "tag": "a",
                "class": "",
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "other_names": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sbox fixidtab",
                        "id": "info"
                    },
                    {
                        "tag": "div",
                        "class": "custom_fields",
                        "index": 0,
                    }   
                ],
                "tag": "span",
                "class": "valor",
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "rating": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "starstruck-rating"
                    }
                ],
                "tag": "span",
                "class": "dt_rating_vgs",
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            },
            "released_date": {
                "containers": [
                    {
                        "tag": "div",
                        "class": "sheader"
                    },
                    {
                        "tag": "div",
                        "class": "data"
                    },
                    {
                        "tag": "div",
                        "class": "extra"
                    }
                ],
                "tag": "span",
                "class": "date",
                "settings": [
                    {
                        "action": "getText"
                    },
                    {
                        "action": "trim",
                        "status": True
                    }
                ]
            }
        }
    }
}


router = APIRouter(prefix="/api/v1/anime")

def exec_settings_in_tag(data_in, settings = []):
    for setting in settings:
        if setting["action"] == "getText":
            data_in = data_in.getText()
        elif setting["action"] == "trim":
            data_in = data_in.strip()
        elif setting["action"] == "split":
            data_in = data_in.split(setting["separator"])
            if "select" in setting:
                data_in = data_in[setting["select"]]
        elif setting["action"] == "replace":
            data_in = data_in.replace(setting["source"], setting["with"])
    
    return data_in

def dig_tag(root, elements):
    data = None
    for element in elements:
        #print("Searching tag: {} with class {}".format(element["tag"], element["class"]))
        data = root.find(element["tag"], {"class": element["class"]})
        #print("Data obtained: {}".format(data))
        if "attribute" in element:
            data = data[element["attribute"]]

    if data and "settings" in element:
        data = exec_settings_in_tag(data, element["settings"])
    
    return data

def iterate_over_containers(sp, containers):
    dst_tag = sp
    for c in containers:
        tag = c["tag"]
        tag_class = c["class"] if "class" in c else ""
        tag_id = c["id"] if "id" in c else ""
        print("Searching {} {} {}".format(tag, tag_class, tag_id))
        if "index" in c:
            idx = c["index"]
            dst_tag = dst_tag.find_all(
                tag, {"class": tag_class, "id": tag_id})[idx]
        else:
            dst_tag = dst_tag.find(tag, {"class": tag_class, "id": tag_id})

    return dst_tag

def parse_element(e_container, a_item, e_tag, e_class, e_id):
    _element = None

    if "type" in a_item:
        # Es un item de tipo lista, iterar sobre sus elementos aplicando las configuraciones
        if a_item["type"] == "list":
            _elements = e_container.find_all(e_tag, {"class": e_class, "id": e_id})
            _element = []
            for _e in _elements:
                _element.append(exec_settings_in_tag(_e, a_item["settings"]))
    else:
        _element = e_container.find_all(e_tag, {"class": e_class, "id": e_id})
        idx = a_item["index"] if "index" in a_item else 0
        _element = _element[idx]
        if "attribute" in a_item:
            _element = _element[a_item["attribute"]]
        if "settings" in a_item:
            _element = exec_settings_in_tag(_element, a_item["settings"])

    return _element

def perform_replace(source, values ):
    if "{number}" in source:
        source = source.replace("{number}", values["number"])
    if "{id}" in source:
        source = source.replace("{id}", values["id"])
    return source

def generate_episodes_data(start, end, config, anime_id):
    episodes = []
    for i in range(start, end):
        title_parsed: str = perform_replace(
            config["title"], {"number": str(i), "id": anime_id})
        link_parsed: str = perform_replace(
            config["link"], {"number": str(i), "id": anime_id})

        episodes.append({
            "title": title_parsed,
            "link": link_parsed
        })
    return episodes

def parse_episodes_element(config, container, id = ""):
    episodes = []
    if config["type"] == "paginated":
        list_container = config["list_container"]
        l_tag = list_container["tag"]
        l_class = list_container["class"] if "class" in list_container else ""
        l_id = list_container["id"] if "id" in list_container else ""
        _elements : list = container.find_all(l_tag, { "class": l_class, "id": l_id })
        _first = _elements[0]
        _last = _elements[-1]
        first_ep = int(_first.find(config["start"]["tag"])[config["start"]["attribute"]])
        if first_ep == 0:
            first_ep += 1
        
        last_ep = int(_last.find(config["end"]["tag"])[config["end"]["attribute"]])
        
        episodes = generate_episodes_data(first_ep, last_ep, config, id)

    return episodes

#has_next_req = requests.get(url, params={"page": page + 1})
#has_next = has_next_req.status_code == 200

@router.get("/{page}/popular")
def get_popular_list(page: str, request: Request):
    if page not in configs:
        return JSONResponse({"error": "El servicio aun no ha sido agregado, por favor intenta con otro"}, 400)

    site_config = configs[page]
    base_url = site_config["base_url"]
    if "popular_section" not in site_config:
        return JSONResponse(
            {
                "error":"La seccion a la que se está intentando acceder no ha sido configurada o no existe en el sitio"
            },
            500)

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

        elements_list = site_soup.find_all(
            dig_in["element"], {"class": dig_in["class"]})

        if len(elements_list) == 0:
            return JSONResponse({"error": "No se ha encontrado ningun elemento en la seccion configurada. Por favor cambie el esquema de busqueda"}, 500)

        # TODO: Implementar la busqueda de paginacion
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
    if page not in configs:
        return JSONResponse({"error": "El servicio aun no ha sido agregado, por favor intenta con otro"}, 400)

    site_config = configs[page]
    base_url = site_config["base_url"]
    lrs_config = site_config["latest_releases_section"]
    url = "{}/{}".format(base_url, lrs_config["path"])

    query_params = {}
    if "params" in lrs_config:
        for param in lrs_config["params"]:
            if param in request.query_params._dict:
                query_params[param]: request.query_params.get(param)

    site_res = requests.get(url, params=query_params)
    try:
        site_soup = bs(site_res.text, "html.parser")
        list_tag = lrs_config["container"]["element"]
        list_class = lrs_config["container"]["class"]
        children_tag = lrs_config["container"]["children"]["tag"]
        children_class = lrs_config["container"]["children"]["class"]

        recent_added_list = site_soup.find(list_tag, { "class": list_class }).find_all(children_tag, { "class": children_class })
        
        if len(recent_added_list) == 0:
            return JSONResponse({
                "error": "No se ha encontrado ningun elemento en la sección configurada. Por favor cambie el esquema de busqueda"
            }, 500)

        results = []

        for rec in recent_added_list:
            episode_title = dig_tag(rec, lrs_config["title"])
            episode_id = dig_tag(rec, lrs_config["episode_id"])
            episode_image = dig_tag(rec, lrs_config["episode_image"])
            episode_number = dig_tag(rec, lrs_config["episode_number"])
            results.append({
                "link_id": episode_id,
                "title": episode_title,
                "image":  episode_image,
                "number": episode_number
            })

        return JSONResponse({"data": results, "total": len(results)}, 200)
    except Exception as ex:
        print(ex)
        return JSONResponse({"error": "Ha ocurrido un error al obtener el contenido"}, 500)

enabled_tags = ["image", "title", "type",
                "rating", "summary", "genre", 
                "other_names", "next_ep_date", 
                "status", "released_date"]


@router.get("/{page}/details/{id}")
async def get_anime_details(page: str, id: str, request: Request):
    if page not in configs:
        return JSONResponse({"error": "El servicio aun no ha sido agregado, por favor intenta con otro"}, 400)

    site_config = configs[page]
    base_url = site_config["base_url"]
    details_config = site_config["anime_details_section"]
    url = "{}/{}/{}".format(base_url, details_config["path"], id)

    query_params = {}
    if "params" in details_config:
        for param in details_config["params"]:
            if param in request.query_params._dict:
                query_params[param]: request.query_params.get(param)

    site_res = requests.get(url, params=query_params)
    #print(site_res.html.raw_html)
    try:
        site_soup = bs(site_res.content, "html.parser")
        out = {}
        for key in list(details_config.keys()):
            print("Element: {}".format(key))
            if key in enabled_tags:
                actual_item = details_config[key]
                # Empezar a manipular
                # primero se debe de iterar sobre "containers"
                element_container = iterate_over_containers(site_soup, actual_item["containers"])
                e_tag = actual_item["tag"]
                e_class = actual_item["class"] if "class" in actual_item else ""
                e_id = actual_item["id"] if "id" in actual_item else ""
                # Luego, con base al tipo de elemento, obtener los datos
                _element = parse_element(element_container, actual_item, e_tag, e_class, e_id)
                # Se crea la entrada "key" con el valor obtenido
                out[key] = _element
            elif key == "episodes":
                actual_item = details_config[key]
                element_container = iterate_over_containers(site_soup, actual_item["containers"])
                if actual_item["type"] == "dynamic":
                    print("Re-loading with JS")
                    asession = AsyncHTMLSession()
                    site_res = await asession.get(url, params=query_params)
                    await site_res.html.arender()
                    asession.close()
                    site_soup = bs(site_res.html.raw_html, "html.parser")
                    element_container = iterate_over_containers(site_soup, actual_item["containers"])
                    
                    
                print(element_container)

                out["episodes"] = parse_episodes_element(actual_item, element_container, id)


        return JSONResponse(out, 200)

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
