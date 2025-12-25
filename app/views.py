from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_upload(request):
    if request.method == "GET":
        return render(request, "test_upload.html")

    return HttpResponse("POST reçu ✅")


