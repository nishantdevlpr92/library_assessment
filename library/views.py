from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Book, Author, Favorite
from .serializers import BookSerializer, AuthorSerializer
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer, UserLoginSerializer, FavoriteSerializer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        search_query = self.request.query_params.get('search', None)
        queryset = super().get_queryset()
        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query)|Q(author__name__icontains=search_query))
        return queryset


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def add_favorite(self, request):
        if request.user.favorites.count() >= 20:
            return Response({'error': 'You can add maximum 20 favorite books.'}, status=400)

        book_id = request.data.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=404)
        
        if Favorite.objects.filter(user=request.user, book=book).exists():
           return Response({'error': 'This book is already in your favorites.'}, status=400)


        Favorite.objects.create(user=request.user, book=book)
        recommendations = self.get_recommendations(request.user, new_favorite=book)
        return Response({
            'status': 'book added to favorites',
            'recommendations': recommendations
        })

    @action(detail=False, methods=['post'])
    def remove_favorite(self, request):
        book_id = request.data.get('book_id')
        favorite = Favorite.objects.get(user=request.user, book__id=book_id)
        favorite.delete()
        return Response({'status': 'book removed from favorites'})

    def get_recommendations(self, user, new_favorite=None):
        favorites = user.favorites.all()
        favorite_books = [fav.book for fav in favorites]

        if new_favorite:
            favorite_books = [new_favorite]
        
        if not favorite_books:
            return []

        all_books = list(Book.objects.all())

        # Create TF-IDF matrix
        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform([book.category for book in all_books])
        favorite_indices = [all_books.index(book) for book in favorite_books]
        
        # Calculate cosine similarity
        cosine_sim = linear_kernel(tfidf_matrix[favorite_indices], tfidf_matrix)

        # Get the scores and recommendations
        scores = list(enumerate(cosine_sim.mean(axis=0)))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Get the top 5 recommendations
        recommended_indices = [i[0] for i in scores if i[0] not in favorite_indices][:5]
        recommended_books = [all_books[i] for i in recommended_indices]
        
        return BookSerializer(recommended_books, many=True).data

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        return Response(self.get_recommendations(request.user))