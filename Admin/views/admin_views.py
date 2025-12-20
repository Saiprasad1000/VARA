from .common_importers import *

@admin_required
def admin_home(request):
    return render(request,'admin_home.html')

@admin_required
def sales_report(request):
    return render(request,'sales_report.html')

@admin_required
def coupon(request):
    return render(request,'coupon.html')

@admin_required
def banner_management(request):
    return render(request,'banner_management.html')

