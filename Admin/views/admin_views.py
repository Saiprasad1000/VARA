from .common_importers import *

def admin_home(request):
    return render(request,'admin_home.html')

def sales_report(request):
    return render(request,'sales_report.html')

def coupon(request):
    return render(request,'coupon.html')

def banner_management(request):
    return render(request,'banner_management.html')

