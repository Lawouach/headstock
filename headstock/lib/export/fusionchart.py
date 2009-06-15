# -*- coding: utf-8 -*-

from bridge import Document as D
from bridge import Element as E

__all__ = ['V3LineExporter']

class V3LineExporter(object):
    @staticmethod
    def export(start, end, data):
        import pprint
        pprint.pprint(data)

        attrs = {u'setAdaptiveYMin': u'1', 
                 u'outCnvBaseFontSize': u'12', u'showSum': u'1', u'showValues': u'0', u'animation': u'0',
                 u'xAxisName': u'', u'yAxisName': u'', u'showAlternateHGridColor': u'0',
                 u'bgColor': u'fcfdfd', u'labelDisplay': u'ROTATE', u'slantLabels': u'1',
                 u'formatNumber': u'0', u'formatNumberScale': u'0', u'showPlotBorder': u'0',
                 u'showBorder': u'0', u'canvasBorderThickness': u'1', u'labelStep': u'2',
                 u'toolTipBorderColor': u'2e6e9e', u'toolTipBgColor': u'fcfdfd'}

        doc = D()
        chart = E(u'chart', attributes=attrs, parent=doc)

        cats = E(u'categories', attributes={u'fontSize': u'12'}, parent=chart)
        for type in data:
            print type
            E(u'category', attributes={u'label': unicode(type)}, parent=cats)
         
        return doc

    @staticmethod
    def write(doc, stream):
        stream.write(doc.xml(indent=True))

    @staticmethod
    def dump(doc, filepath):
        f = file(filepath, 'w')
        f.write(doc.xml(indent=True))
        f.close()
        
