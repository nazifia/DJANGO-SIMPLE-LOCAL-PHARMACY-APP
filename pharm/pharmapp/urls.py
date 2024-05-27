from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('search/', views.search, name='search'),
    path('store/', views.store, name='store'),
    path('edit_item/<int:pk>', views.edit_item, name='edit_item'),
    path('add_to_cart/<int:pk>', views.add_to_cart, name='add_to_cart'),
    path('add_to_store/', views.add_to_store, name='add_to_store'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('remove_from_cart/<int:pk>', views.remove_from_cart, name='remove_from_cart'),
    path('receipt/', views.generate_receipt, name='receipt'),
    path('logs/', views.activity_logs, name='logs'),
    path('Dlogs/', views.deduction_logs, name='Dlogs'),
    path('activities/', views.activities, name='activities'),
    path('daily/', views.daily_sales, name='daily_sales'),
    path('monthly/', views.monthly_sales, name='monthly_sales'),
    path('sales/', views.sales, name='sales'),
    path('loans/', views.loan_list, name='loan_list'),
    path('add_loan/', views.add_loan, name='add_loan'),
    path('edit_loan/<int:pk>/', views.edit_loan, name='edit_loan'),
    path('delete_loan/<int:pk>/', views.delete_loan, name='delete_loan'),
    path('register_customer/', views.register_customer, name='register_customer'),
    path('customer_list/', views.customer_list, name='customer_list'),
    path('customer/delete/<int:pk>/', views.delete_customer, name='delete_customer'),
    path('apply_discount/<int:pk>/', views.apply_discount, name='apply_discount'),
]