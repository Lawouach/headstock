# -*- coding: utf-8 -*-
import time
from amplee.atompub.member import MemberResource
from amplee.error import ResourceOperationException
from amplee.utils import extract_url_trail

__all__ = ['ResourceWrapper', 'ProfileResource']

class ResourceWrapper(MemberResource):
    def generate_resource_id(self, entry=None, slug=None, info=None):
        if slug:
            return slug.replace(' ','_').decode('utf-8')
        else:
            # if not then we use the last segment of the
            # link as the id of the resource in the storage
            links = entry.xml_xpath('/atom:entry/atom:link[@rel="edit"]')
            if links:
                return extract_url_trail(links[0].href)

        # fallback
        return str(time.time())

class ProfileResource(MemberResource):
    def generate_resource_id(self, entry=None, slug=None, info=None):
        if slug:
            return slug.replace(' ','_').decode('utf-8')
        else:
            # if not then we use the last segment of the
            # link as the id of the resource in the storage
            links = entry.xml_xpath('/atom:entry/atom:link[@rel="edit"]')
            if links:
                return extract_url_trail(links[0].href)

        # fallback
        return str(time.time())
