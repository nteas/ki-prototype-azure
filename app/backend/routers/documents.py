from quart import (
    Blueprint,
    Quart,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
    send_file,
    send_from_directory,
)

document_router = Blueprint("documents", __name__, url_prefix="/documents")


# get list og files from blob storage
@document_router.route("/files", methods=["GET"])
async def get_files():
    blob_container_client = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    blob_list = blob_container_client.list_blobs()
    # convert blob_list from AsyncItemPaged to list
    blob_list = [blob async for blob in blob_list]

    blob_names = []
    for blob in blob_list:
        blob_names.append(blob.name)
    return {"files": blob_names}


# search for file name in cognitive search
@document_router.route("/search", methods=["GET"])
async def search():
    search_client = current_app.config[CONFIG_SEARCH_CLIENT]
    search_term = request.args.get("q")
    search_results = await search_client.search(search_text=search_term, include_total_count=True)
    search_results = [result async for result in search_results]
    return {"results": search_results}
