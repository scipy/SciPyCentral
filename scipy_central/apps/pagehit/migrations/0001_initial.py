# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PageHit'
        db.create_table('pagehit_pagehit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ua_string', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('item', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('item_pk', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('pagehit', ['PageHit'])


    def backwards(self, orm):
        
        # Deleting model 'PageHit'
        db.delete_table('pagehit_pagehit')


    models = {
        'pagehit.pagehit': {
            'Meta': {'object_name': 'PageHit'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'item': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'item_pk': ('django.db.models.fields.IntegerField', [], {}),
            'ua_string': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['pagehit']
