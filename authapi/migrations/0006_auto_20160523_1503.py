# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-23 15:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authapi', '0005_auto_20160523_1459'),
    ]

    operations = [
        migrations.RenameField(
            model_name='seedorganization',
            old_name='modified_at',
            new_name='updated_at',
        ),
        migrations.RenameField(
            model_name='seedpermission',
            old_name='modified_at',
            new_name='updated_at',
        ),
        migrations.RenameField(
            model_name='seedteam',
            old_name='modified_at',
            new_name='updated_at',
        ),
    ]