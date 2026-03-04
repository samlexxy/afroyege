from django.contrib.auth import get_user_model

from lib_util.fields import UpdateUserField
from django.db import models
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist


# Create your models here.

# User = get_user_model()


class AuditModel(models.Model):
    """Records the user who created or changed an object.

    Adds fields which record:
    - who created the model and when
    - who did the last change and when

    Meant to be sub-classed by models.
    """

    creation_date = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        null=True,
    )
    creation_user = UpdateUserField(
        editable=False,
        related_name="+"
    )

    last_modified_date = models.DateTimeField(
        auto_now=True,
        editable=False
    )
    last_modified_user = UpdateUserField(
        editable=False,
        related_name="+"
    )

    # objects manager should not be provided here as this class is abstract

    class Meta:
        abstract = True

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
        # Todo: make this a required argument (difficult!)
        # Then we can remove one need for thread locals
        last_modified_user=None,
        last_modified_date=None,
        **kwargs
    ):
        from lib_util.middleware import get_current_user #noqa

        self.last_modified_user = last_modified_user or get_current_user()
        self.last_modified_date = last_modified_date or timezone.now()
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.update({"last_modified_user", "last_modified_date"})
        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields, **kwargs
        )
    

class ActiveManager(models.Manager):
    """Manager that only returns non-deleted by default"""
    SOFT_DELETE_FIELDS = ("is_deleted", "deleted")

    def get_queryset(self):
        # qs = super().get_queryset()

        # for name in self.SOFT_DELETE_FIELDS:
        #     try:
        #         self.model._meta.get_field(name)
        #     except FieldDoesNotExist:
        #         continue
        #     return qs.filter(**{name: False})
        # return qs
        return super().get_queryset().filter(is_deleted=False)


class BaseModel( 
    AuditModel, # you can add mixins to this later on
):

    """Convenience class for models inheriting from both the parents

    Also provides the standard answer to the the question
    'can this thing be deleted?', i.e. 'No'.
    """

    # objects = ActiveManager()
    # all_objects = models.Manager()

    class Meta:
        abstract = True