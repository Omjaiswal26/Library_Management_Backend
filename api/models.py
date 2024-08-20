from django.db import models

class Members(models.Model):
    member_id = models.AutoField(primary_key=True)
    member_name = models.CharField(max_length=50)
    member_email = models.EmailField()
    member_phone = models.IntegerField()
    joining_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    outstanding_debt = models.IntegerField(default=0)
    books_issued = models.PositiveIntegerField(default=0)
    last_settlement_date = models.DateField(blank=True, null=True)
    last_settled_amount = models.IntegerField(default=0)

class IssuedBooks(models.Model):
    book_id = models.IntegerField()
    book_title = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255)
    issued_to_member = models.ForeignKey(Members, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now=True)
    return_date = models.DateField()
    overdue = models.IntegerField(default=0)
    fine = models.IntegerField(default= 0)
    status = models.CharField(max_length=50)


class BookStock(models.Model):
    book_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=0)