# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'PageHit.extra_info'
        db.alter_column('pagehit_pagehit', 'extra_info', self.gf('django.db.models.fields.CharField')(max_length=2083, null=True))

    def backwards(self, orm):

        # Changing field 'PageHit.extra_info'
        db.alter_column('pagehit_pagehit', 'extra_info', self.gf('django.db.models.fields.CharField')(max_length=512, null=True))

    models = {
        'pagehit.pagehit': {
            'Meta': {'object_name': 'PageHit'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'extra_info': ('django.db.models.fields.CharField', [], {'max_length': '2083', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'item': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'item_pk': ('django.db.models.fields.IntegerField', [], {}),
            'ua_string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['pagehit']