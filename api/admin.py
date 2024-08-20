from django.contrib import admin
from .models import *


class MembersAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'member_name', 'member_email')

class IssuedBooksAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'issued_to_member', 'issue_date', 'return_date', 'fine' )
admin.site.register(Members, MembersAdmin)
admin.site.register(IssuedBooks, IssuedBooksAdmin)

