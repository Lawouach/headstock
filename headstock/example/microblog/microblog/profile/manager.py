# -*- coding: utf-8 -*-
import os.path
import shutil
from string import letters, digits
from random import choice

from amplee.error import UnknownResource
from amplee.utils import get_isodate, generate_uuid_uri

from headstock.api.profile import Profile
from headstock.api.dataform import Data, Field

from bridge import Element as E
from bridge.common import ATOM10_NS, ATOM10_PREFIX
from bridge.filter.atom import lookup_entry

from microblog.profile.user import UserProfile

__all__ = ['ProfileManager']

class ProfileManager(object):
    @staticmethod
    def load_profiles(base_dir, atompub):
        profiles = {}
        store = atompub.service.store
        for workspace in atompub.service.workspaces:
            if workspace.name_or_id == 'workspace-profile':
                continue
            profile_name = workspace.name_or_id.replace('workspace-', '')
            if profile_name not in profiles:
                p = ProfileManager.load_profile(base_dir, atompub, profile_name)
                if p: 
                    profiles[p.name] = p 
        return profiles

    @staticmethod
    def load_profile(base_dir, atompub, profile_name):
        store = atompub.service.store
        info = store.get_content_info(profile_name, 'profile.xml')
        try:
            profile = store.fetch_content(info)
        except UnknownResource:
            print "Unknown profile: %s" % profile_name
        else:
            p = Profile.from_profile_element(E.load(profile).xml_root)
            return UserProfile(profile_name, p)

    @staticmethod
    def has_profile(atompub, profile_name):
        store = atompub.service.store
        info = store.get_content_info(profile_name, 'profile.xml')
        return store.exists(info) or store.exists(info, as_media=True)

    @staticmethod
    def store_profile(atompub, profile):
        profile_xml = profile.xml()

        store = atompub.service.store
        store.storage.create_container(profile.name)
        info = store.get_content_info(profile.name, 'profile.xml')
        store.storage.put_content(info, profile_xml)

    @staticmethod
    def delete_profile(atompub, profile):
        store = atompub.service.store
        info = store.get_content_info(profile.name, '')
        path = os.path.normpath(info.key)
        if os.path.exists(path) and os.path.isdir(path):
            # I don't feel at ease with that call...
            shutil.rmtree(path)
            
    @staticmethod
    def get_profile_password(base_dir, profile_name):
        pwd_file = os.path.join(base_dir, 'etc', 'password')
        for line in file(pwd_file, 'r'):
            line = line.strip()
            if line:
                name, password = line.split(':')
                if name == profile_name:
                    return password

    @staticmethod
    def set_profile_password(base_dir, profile_name):
        pwd_file = os.path.join(base_dir, 'etc', 'password')
        pwd = ''.join([choice(letters+digits) for _ in range(0, 9)])
        lines = ['%s:%s' % (profile_name, pwd)]
        for line in file(pwd_file, 'r'):
            line = line.strip()
            if line:
                name, password = line.split(':')
                if name != profile_name:
                    lines.append(line)
        file(pwd_file, 'w').write('\n'.join(lines))
        return pwd
