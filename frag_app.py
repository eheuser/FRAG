import gzip
import logging
import json
import os
from operator import itemgetter
import time
import threading

import webbrowser
from flask import Flask, request, make_response
from werkzeug.utils import secure_filename

from utils.utils import read_llm_config
from modules.frag import FRAG
from modules.obj import QueryStateManager, ArtifactStateManager
from views.query_views import data_query, stream_query
from views.config_views import update_config, get_artifact_files, monitor_parse_progress, parse_upload_folder, delete_vector_db

def create_ui_service(logger):

    _logger = logging.getLogger("werkzeug")
    if _logger:
        _logger.setLevel(logging.ERROR)

    app = Flask(__name__)
    app.config.update({"DEBUG": False})
    site_dir = "site/"

    # Setup working dirs
    data_dir = "data/"
    upload_dir = "upload/"

    setup_dirs = [
        data_dir,
        upload_dir,
    ]

    for _d in setup_dirs:
        if os.path.isdir(_d) is False:
            os.mkdir(_d)

    # FRAG object is a wrapper around the Vector DB object that handles artifacts
    frag = FRAG(logger)

    # Query State Manager Object
    # - tracks LLM query status
    query_state_manager = QueryStateManager()

    # Artifact State Manager Object
    artifact_state_manager = ArtifactStateManager()

    @app.route("/delete_db", methods=["GET"])
    def api_delete_db():
        try:
            result = delete_vector_db(frag, logger)
            
            content = gzip.compress(json.dumps(result).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_delete_db: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response

    @app.route("/progress", methods=["GET"])
    def api_monitor_parse_progress():
        try:
            result = monitor_parse_progress(artifact_state_manager, logger)
            
            content = gzip.compress(json.dumps(result).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_monitor_parse_progress: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/upload", methods=["POST"])
    def upload_artifact():
        try:
            uploaded_files = request.files.getlist("file")
            file_tups = [ ]
            for file in uploaded_files:
                try:
                    byte_string = file.read()
                except Exception as e:
                    logger.critical(f"upload_artifact: Saving file raised {e}")
                    continue
                file_size = len(byte_string)
                filename = secure_filename(file.filename)
                filepath = f"{upload_dir}{filename}"
                with open(filepath, "wb") as f:
                    f.write(byte_string)
                file_tups.append( ( file_size, filepath ) )
            
            # Sort by smallest file first so the UI updates sooner
            sorted_file_tups = sorted(file_tups,key=itemgetter(0))
            for (sz, fp) in sorted_file_tups:
                artifact_state_manager.add_file(fp)
            
            parse_upload_folder(frag, artifact_state_manager, logger)
            content = gzip.compress(json.dumps( { "response": "OK" } ).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"upload_artifact: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/artifact_files", methods=["GET"])
    def api_artifact_files():
        try:
            result = get_artifact_files(frag, logger)

            content = gzip.compress(json.dumps(result).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_artifact_files: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response

    @app.route("/update_config", methods=["POST"])
    def api_update_config():
        try:
            query_dict = request.get_json()
            new_config = query_dict.get("config", {})
            result = update_config(new_config, logger)
            
            content = gzip.compress(json.dumps(result).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_update_config: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response

    @app.route("/config", methods=["GET"])
    def api_get_config():
        try:
            config = read_llm_config(logger)

            content = gzip.compress(json.dumps(config).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_get_config: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/query", methods=["POST"])
    def api_data_query():
        try:
            query_dict = request.get_json()
            content = data_query(query_dict, frag, logger)

            content = gzip.compress(json.dumps(content).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_data_query: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/stream", methods=["POST"])
    def api_stream_query():
        try:
            query_dict = request.get_json()
            llm_config = read_llm_config(logger)

            content = stream_query(query_dict, frag, query_state_manager, llm_config, logger)

            content = gzip.compress(json.dumps(content).encode("utf8"))
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/json"
            return response
        except Exception as e:
            logger.critical(f"api_stream_query: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response

    @app.route("/")
    def file_ui():
        try:
            fpath = f"{site_dir}ui.html"

            with open(fpath, "rb") as f:
                content = gzip.compress(f.read(), 1)
            
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "text/html"
            return response
        except Exception as e:
            logger.critical(f"file_ui: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/favicon.ico")
    def file_favicon():
        try:
            fpath = f"{site_dir}favicon.ico"

            with open(fpath, "rb") as f:
                content = gzip.compress(f.read(), 1)

            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            return response
        except Exception as e:
            logger.critical(f"file_favicon: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/js/<fname>")
    def file_js(fname):
        try:
            fpath = f"{site_dir}js/{fname}"

            with open(fpath, "rb") as f:
                content = gzip.compress(f.read(), 1)

            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "application/javascript"
            return response
        except Exception as e:
            logger.critical(f"file_favicon: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/css/<fname>")
    def file_styles(fname):
        try:
            fpath = f"{site_dir}css/{fname}"

            with open(fpath, "rb") as f:
                content = gzip.compress(f.read(), 1)
            
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "text/css"
            return response
        except Exception as e:
            logger.critical(f"file_styles: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response
        
    @app.route("/img/<fname>")
    def file_img(fname):
        try:
            fpath = f"{site_dir}img/{fname}"

            with open(fpath, "rb") as f:
                content = gzip.compress(f.read(), 1)
            
            response = make_response(content)
            response.headers["Content-Length"] = len(content)
            response.headers["Content-Encoding"] = "gzip"
            response.content_type = "image/png"
            return response
        except Exception as e:
            logger.critical(f"file_img: Raised {e}")
            response = make_response(json.dumps( { "response": f"{e}" } ))
            response.content_type = "application/json"
            return response

    # Delay open browser
    _ = threading.Thread(target=delayed_browser).start()

    return app

def delayed_browser(seconds=1):
    time.sleep(seconds)
    webbrowser.open_new("http://127.0.0.1/")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARN, format=f"%(asctime)s.%(msecs)03d %(levelname)s:%(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    app = create_ui_service(logger)
    app.run(debug=False, use_reloader=False, use_debugger=False, port=80, host="127.0.0.1", threaded=True)