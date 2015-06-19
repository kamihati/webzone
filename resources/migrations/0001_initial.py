# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rs_type', models.SmallIntegerField(default=1, verbose_name='\u7d20\u6750\u7c7b\u522b', choices=[(1, '\u516c\u5171\u7d20\u6750\u7c7b\u522b'), (2, '\u4e2a\u4eba\u7d20\u6750\u7c7b\u522b')])),
                ('name', models.CharField(max_length=20, verbose_name='\u98ce\u683c\u540d\u79f0')),
                ('user_id', models.IntegerField(verbose_name='\u521b\u5efa\u4ebaid')),
                ('status', models.SmallIntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u6b63\u5e38'), (1, '\u5df2\u5220\u9664')])),
                ('create_time', models.DateTimeField(default=datetime.datetime(2015, 3, 27, 15, 31, 5, 613000))),
            ],
            options={
                'db_table': 'resource_style',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rs_type', models.SmallIntegerField(default=1, verbose_name='\u7d20\u6750\u7c7b\u522b', choices=[(1, '\u516c\u5171\u7d20\u6750\u7c7b\u522b'), (2, '\u4e2a\u4eba\u7d20\u6750\u7c7b\u522b')])),
                ('name', models.CharField(max_length=20, verbose_name='\u5206\u7c7b\u540d\u79f0')),
                ('user_id', models.IntegerField(verbose_name='\u521b\u5efa\u4ebaid')),
                ('status', models.SmallIntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u6b63\u5e38'), (1, '\u5df2\u5220\u9664')])),
                ('create_time', models.DateTimeField(default=datetime.datetime(2015, 3, 27, 15, 31, 5, 612000))),
            ],
            options={
                'db_table': 'resource_type',
            },
            bases=(models.Model,),
        ),
    ]
