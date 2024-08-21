from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from rest_framework import status
from .models import *
from .serializers import *
from django.core.paginator import Paginator
import urllib.parse

class BooksListAPI(APIView):
    def get(self, request):
        count = int(request.GET.get('count', 20))
        page = int(request.GET.get('page', 1))
        title = request.GET.get('title')
        authors = request.GET.get('authors')
        url = "https://frappe.io/api/method/frappe-library"
        books = []
        max_pages = 200  # Limit to prevent infinite loops

        while len(books) < count and page <= max_pages:
            params = {'page': page}
            if title:
                params.update({"title": title})
            if authors:
                params["authors"] = authors
            try:
                frappe_response = requests.get(url, params=params)
                response_data = frappe_response.json()

                if frappe_response.status_code == 200:
                    fetched_books = response_data.get('message', [])
                    for book in fetched_books:
                        book_id = book.get('bookID')
                        if IssuedBooks.objects.filter(book_id=book_id, status="Issued").exists():
                            book['status'] = "Issued"
                        else:
                            book['status'] = "Available"
                        books.append(book)
                    if not fetched_books:
                        break  # Exit if no more books are returned
                    page += 1
                else:
                    return Response({'error': 'Failed to fetch data'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:

                return Response({'error': e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(books[:count], status=status.HTTP_200_OK)

class MembersAPI(APIView):
    def get(self, request):
        count = request.GET.get('count')

        try:
            count = int(count)  # Ensure count is an integer
        except (TypeError, ValueError):
            count = None

        members = Members.objects.all()

        if count:
            members = members[:count]

        serialized_members = MembersSerializer(members, many=True)
        return Response(serialized_members.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MembersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MembersPageAPI(APIView):
    def get(self, request):
        # Get page and page_size from request parameters
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('count', 20)  # Default page size is 20

        try:
            page_number = int(page_number)
            page_size = int(page_size)
        except (TypeError, ValueError):
            page_number = 1
            page_size = 20

        # Fetch all members
        members = Members.objects.all()

        # Apply pagination
        paginator = Paginator(members, page_size)
        try:
            page = paginator.page(page_number)
        except EmptyPage:
            return Response([], status=status.HTTP_404_NOT_FOUND)

        serialized_members = MembersSerializer(page.object_list, many=True)

        # Return paginated data
        return Response({
            'total_pages': paginator.num_pages,
            'current_page': page_number,
            'total_members': paginator.count,
            'members': serialized_members.data
        }, status=status.HTTP_200_OK)


class IssuedBooksListAPI(APIView):
    def get(self, request):
        count = request.GET.get('count')

        issued_books = IssuedBooks.objects.filter(status = "Issued")

        if count:
            count = int(count)
            issued_books = issued_books[:count]

        serialized_issued_books = IsssuedBooksSerializer(issued_books, many=True)
        return Response(serialized_issued_books.data, status=status.HTTP_200_OK)


class IssuedBooksAPI(APIView):
    def get(self, request):
        book_id = request.GET.get('book_id')

        if not book_id:
            return Response({'message': 'Book Id is requried'})

        issued_book = IssuedBooks.objects.filter(book_id = book_id, status="Issued").first()

        if not issued_book:
            return Response({'message': 'Book not issued yet'}, status=status.HTTP_404_NOT_FOUND)

        serializer_issued_book = IsssuedBooksSerializer(issued_book)
        return Response(serializer_issued_book.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        serializer = IsssuedBooksSerializer(data = data, partial = True)

        if serializer.is_valid():
            issued_book = serializer.save()

            # Increase the books_issued count for the member
            member = issued_book.issued_to_member
            member.books_issued += 1
            member.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        book_id = request.data.get('book_id')
        issued_book = IssuedBooks.objects.filter(book_id=book_id, status = "Issued").first()

        today = timezone.now().date()
        
        if not issued_book:
            return Response({'error' : 'Issued book not found'}, status=status.HTTP_404_NOT_FOUND)

        member = issued_book.issued_to_member
        member.books_issued -= 1
        rent_days = (today - issued_book.issue_date).days
        if issued_book.issue_date==today:
            rent_days = 1

        member.outstanding_debt += (rent_days*10)
        issued_book.overdue = (today - issued_book.return_date).days
        issued_book.fine = issued_book.overdue * 20
        member.outstanding_debt += issued_book.fine
        
        member.save()
        issued_book.status = 'Returned'
        issued_book.save()
        return Response({'message' : 'Issued Book returned successfully'}, status=status.HTTP_200_OK)


class OverDueBookList(APIView):
    def get(self, request):
        count = int(request.GET.get('count',20))
        today = timezone.now().date()

        overdue_books = IssuedBooks.objects.filter(return_date__lt = today, status = "Issued")

        result = []

        for overdue_book in overdue_books:
            overdue_days = (today - overdue_book.return_date).days
            overdue_book.fine = (overdue_days * 20)
            overdue_book.overdue = overdue_days

            overdue_book.save()
            result.append({
                'member_id' : overdue_book.issued_to_member.member_id,
                'member_name' : overdue_book.issued_to_member.member_name,
                'book_id': overdue_book.book_id,
                'book_title': overdue_book.book_title,
                'book_author': overdue_book.book_author,
                'overdue': overdue_book.overdue,
                'fine': overdue_book.fine
            })
        
        return Response(result[:count], status=status.HTTP_200_OK)
    

class SettleMemberDebtAPI(APIView):
    def get(self, request):
        member_id = request.GET.get('member_id')

        member = Members.objects.filter(member_id = member_id).first()

        if not member:
            return Response({"message" : "Invalid Member ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        member.last_settlement_date = timezone.now().date()
        member.last_settled_amount = member.outstanding_debt
        member.outstanding_debt = 0
        member.save()

        return Response({"message" : "Outstanding Settled"}, status=status.HTTP_200_OK)
    

class StatisticsAPI(APIView):
    def get(self, request):
        total_members = Members.objects.count()
        active_members = Members.objects.filter(is_active = True).count()
        issued_books = IssuedBooks.objects.filter(status = "Issued").count()
        returned_books = IssuedBooks.objects.filter(status = "Returned").count()

        data = {
            "total_members" : total_members,
            "active_members" : active_members,
            "issued_books" : issued_books,
            "returned_books" : returned_books
        }
        return Response(data, status=status.HTTP_200_OK)