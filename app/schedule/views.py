import json

from django.http import HttpResponse
from django.http import HttpRequest
from .middleware import load_surf_schedule_data


# Create your views here.
def get_surf_schedule_data(request: HttpRequest, days: int = 3):
    jsondata, comments = load_surf_schedule_data(request, next_days=days)
    jsondata = json.dumps({"data": jsondata}, indent=4)
    return HttpResponse(jsondata, content_type="application/json")


def get_surf_session_comments(request: HttpRequest, days: int = 3):
    _, comments = load_surf_schedule_data(request, next_days=days)

    return comments
