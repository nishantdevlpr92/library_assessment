from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.CharField(max_length=200, null=True, blank=True)
    isbn = models.IntegerField(unique=True)
    price = models.IntegerField(null=True, blank=True)
    rating = models.DecimalField(
        blank=True, null=True, max_digits=20, decimal_places=2
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
    

class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorites', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='favorited_by', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book')