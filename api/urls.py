from django.urls import path, include
from .views import *

urlpatterns = [
    path('books/', BooksListAPI.as_view()),
    path('members/', MembersAPI.as_view()),
    path('issued_books/', IssuedBooksAPI.as_view()),
    path('issued_books_list/', IssuedBooksListAPI.as_view()),
    path('overdue_book_list/', OverDueBookList.as_view()),
    path('settle_member_debt/', SettleMemberDebtAPI.as_view()),
    path('statistics/', StatisticsAPI.as_view()),
    path('members_page/', MembersPageAPI.as_view())
]