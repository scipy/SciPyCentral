from django.shortcuts import render_to_response

def front_page(request):
    return render_to_response('pages/front-page.html')

def about_page(request):
    return render_to_response('pages/about-page.html')

def licence_page(request):
    return render_to_response('pages/about-licenses.html')