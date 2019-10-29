from marshmallow import Schema, fields


class FlashRequestSchema(Schema):
	test_field = fields.Int(required=True)
