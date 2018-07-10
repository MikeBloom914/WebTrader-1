#!/usr/bin/env python3

from flask_marshmallow import Schema, fields


class QuoteSerializer(Schema):
    class Meta:
        fields = ('name',
                  'symbol',
                  'exchange',
                  'last_price',
                  'change_1h',
                  'change_percent_1h',
                  'change_1d',
                  'change_percent_1d',
                  'change_7d',
                  'change_percent_7d',
                  'change_year',
                  'change_percent_year',
                  'timestamp',
                  'market_cap',
                  'volume',
                  'high',
                  'low',
                  'open'
                  )
