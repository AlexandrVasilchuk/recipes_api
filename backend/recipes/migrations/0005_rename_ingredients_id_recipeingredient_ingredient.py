# Generated by Django 3.2 on 2023-06-11 11:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_rename_ingredient_recipeingredient_ingredients_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeingredient',
            old_name='ingredients_id',
            new_name='ingredient',
        ),
    ]
