from fastapi import APIRouter, Request

log_router = APIRouter("logs", __name__)


# @log_router.route("/logs", methods=["GET"])
# async def get_logs():
#     db = current_app.config["mongodb"]
#     logs_cursor = db.logs.find()
#     logs_list = []
#     for log in logs_cursor:
#         log["_id"] = str(log["_id"])  # Convert ObjectId to string
#         logs_list.append(log)
#     return {"logs": logs_list}


# @log_router.route("/logs/add", methods=["POST"])
# async def add_log():
#     try:
#         data = await request.get_json()
#         uuid = data.get("uuid")
#         feedback = data.get("feedback")
#         comment = data.get("comment")
#         timestamp = data.get("timestamp")
#         thought_process = data.get("thought_process")

#         log = {
#             "uuid": uuid,
#             "feedback": feedback,
#             "comment": comment,
#             "timestamp": timestamp,
#             "thought_process": thought_process,
#         }

#         db = current_app.config["mongodb"]
#         db.logs.insert_one(log)

#         return {"success": True}
#     except Exception as e:
#         return {"error": str(e)}
