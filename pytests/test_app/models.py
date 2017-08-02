from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255)
    birth = models.DateField('birth date')

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    state = models.PositiveSmallIntegerField(
        'publisher state',
        choices=(
            (0, 'Active'),
            (1, 'Disabled')
        ),
        default=1
    )

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher)

