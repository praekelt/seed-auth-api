# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-23 14:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authapi', '0004_auto_20160523_1442'),
    ]

    operations = [
        migrations.RenameField(
            model_name='seedorganization',
            old_name='name',
            new_name='title',
        ),
        migrations.RenameField(
            model_name='seedteam',
            old_name='name',
            new_name='title',
        ),
        migrations.AlterField(
            model_name='seedpermission',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
