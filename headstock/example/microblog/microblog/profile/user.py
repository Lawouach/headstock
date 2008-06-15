# -*- coding: utf-8 -*-
from headstock.api.profile import Profile
from headstock.api.dataform import Data, Field

__all__ = ['UserProfile', 'EmptyUserProfile']

class UserProfile(object):
    def __init__(self, name=None, profile=None):
        self.name = name
        self.profile = profile

    @property
    def username(self):
        return self.get('nickname', default='')
        
    @property
    def fullname(self):
        return self.get('fullname', default='')
        
    @property
    def email(self):
        return self.get('email', default='')
        
    @property
    def jid(self):
        return self.get('jid', default='')
        
    @property
    def openid(self):
        return self.get('openid', default='')
        
    @property
    def country(self):
        return self.get('country', default='')
        
    @property
    def url(self):
        return self.get('homepage', default='')
        

    def xml(self):
        return Profile.to_profile_element(self.profile).xml()

    def fill(self, **kwargs):
        d = Data(u'')
        for key in kwargs:
            f = Field(var=unicode(key), values=[unicode(kwargs[key])])
            d.fields.append(f)

        if not self.profile:
            self.profile = Profile()
        self.profile.x = d

    def add(self, key, value):
        field = self.profile.x.field_by_var(key)
        if not field:
            self.profile.x.fields.append(Field(var=key, values=[value]))
        else:
            field.values.append(value)
        
    def get(self, key, default=None):
        if not self.profile or not self.profile.x:
            return default
        
        field = self.profile.x.field_by_var(key)
        if field and field.values:
            return field.values[0] or default

        return default

    def set(self, key, value):
        field = self.profile.x.field_by_var(key)
        if field:
            self.profile.x.fields.remove(field)
        
        self.profile.x.fields.append(Field(var=key, values=[value]))
        

class EmptyUserProfile(UserProfile):
    def get(self, key, default=None):
        return default
