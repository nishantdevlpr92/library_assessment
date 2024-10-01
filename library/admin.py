from django.contrib import admin
from .models import Author, Book, Favorite
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

# Register your models here.


class AuthorAdmin(ImportExportModelAdmin):
    list_display = ("name",)


class BookResource(resources.ModelResource):
    author = fields.Field(
        column_name='author',
        attribute='author',
        widget=ForeignKeyWidget(Author, 'name')  # Use the author's name for import
    )

    class Meta:
        model = Book
        import_id_fields = ('isbn',)
        fields = ('title', 'author', 'category', 'isbn', 'price', 'rating', 'description')


class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    list_display = ("title",)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'book') 



admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Favorite, FavoriteAdmin)