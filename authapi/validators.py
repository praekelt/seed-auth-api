from rest_framework.serializers import ValidationError


class CreateOnly(object):
    def set_context(self, serializer_field):
        # Determine if this is a create or update operation.
        self.is_update = (
            getattr(serializer_field.parent, 'instance', None) is not None)

    def __call__(self, value):
        if self.is_update:
            message = 'This field can only be set on creation.'''
            raise ValidationError(message)
