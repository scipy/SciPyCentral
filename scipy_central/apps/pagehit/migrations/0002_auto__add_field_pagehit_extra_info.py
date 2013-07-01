# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'PageHit.extra_info'
        db.add_column('pagehit_pagehit', 'extra_info', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'PageHit.extra_info'
        db.delete_column('pagehit_pagehit', 'extra_info')


    models = {
        'pagehit.pagehit': {
            'Meta': {'object_name': 'PageHit'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'extra_info': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'item': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'item_pk': ('django.db.models.fields.IntegerField', [], {}),
            'ua_string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['pagehit']
