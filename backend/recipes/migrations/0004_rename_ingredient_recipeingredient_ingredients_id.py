# Generated by Django 3.2 on 2023-06-11 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_rename_ingredient_id_recipeingredient_ingredient'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeingredient',
            old_name='ingredient',
            new_name='ingredients_id',
        ),
    ]