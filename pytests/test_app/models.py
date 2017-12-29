from django.db import models
from django.utils.timezone import now


def default_date():
    return now().date()


class Integers(models.Model):
    f_integer = models.IntegerField('integer', default=-22)
    f_positive_integer = models.PositiveIntegerField('positive integer', default=0)
    f_small_integer = models.SmallIntegerField('small integer', default=13)
    f_positive_small_integer = models.PositiveSmallIntegerField('positive small integer', default=222)

    f_decimal = models.DecimalField('decimal', max_digits=10, decimal_places=4, default=3.1415)
    f_float = models.FloatField('float', default=3.14)
    
    
class CallableDefault(models.Model):
    dt_callable = models.DateField('callable default', default=default_date)

    def __str__(self):
        return self.dt_callable


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
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

