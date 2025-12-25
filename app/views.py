from django.shortcuts import render
from django.http import HttpResponse

def test_upload(request):
    return render(request, "test_upload.html")



